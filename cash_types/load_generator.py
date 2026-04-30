from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request
import argparse
import json
import math
import random
import statistics
import time


WORKLOADS = {
    "read-heavy": 0.80,
    "balanced": 0.50,
    "write-heavy": 0.20,
}

LOAD_LEVELS = {
    "rps-550": {
        "request_multiplier": 1.0,
        "concurrency_multiplier": 1.0,
    },
}

DEFAULT_TARGETS = [
    "cache_aside=http://127.0.0.1:8001",
    "write_through=http://127.0.0.1:8002",
    "write_back=http://127.0.0.1:8003",
]


@dataclass(frozen=True)
class Operation:
    method: str
    item_id: int
    value: str | None = None


@dataclass
class RequestResult:
    ok: bool
    latency_ms: float
    status: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class LoadLevel:
    name: str
    requests: int
    duration: float
    concurrency: int
    target_rps: float


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = parse_targets(args.target or DEFAULT_TARGETS)
    load_levels = build_load_levels(args)

    logs: list[str] = []
    rows: list[dict] = []

    def log(message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        print(line, flush=True)
        logs.append(line)

    log(
        "Starting cache comparison: "
        f"{len(targets)} strategies, {len(WORKLOADS)} workloads, "
        f"{len(load_levels)} RPS levels"
    )

    for target_name, base_url in targets.items():
        wait_for_health(base_url, log)
        for load_index, load_level in enumerate(load_levels, start=1):
            for workload_index, (workload_name, read_ratio) in enumerate(WORKLOADS.items(), start=1):
                operations = build_operations(
                    read_ratio=read_ratio,
                    request_count=load_level.requests,
                    dataset_size=args.dataset_size,
                    hot_set_size=args.hot_set_size,
                    hot_key_ratio=args.hot_key_ratio,
                    seed=args.seed + load_index * 100 + workload_index,
                )

                label = f"{target_name} / {load_level.name} / {workload_name}"
                log(f"{label}: reset database and cache")
                post_json(f"{base_url}/admin/reset", {"dataset_size": args.dataset_size})

                log(
                    f"{label}: load started "
                    f"(target_rps={load_level.target_rps}, "
                    f"requests={load_level.requests}, "
                    f"concurrency={load_level.concurrency})"
                )
                result = run_workload(
                    base_url=base_url,
                    operations=operations,
                    duration_seconds=load_level.duration,
                    concurrency=load_level.concurrency,
                )
                metrics_before_flush = get_json(f"{base_url}/metrics")
                flush_result = post_json(f"{base_url}/admin/flush", {})
                metrics_after_flush = get_json(f"{base_url}/metrics")

                row = build_result_row(
                    target_name=target_name,
                    load_level=load_level,
                    workload_name=workload_name,
                    generator_result=result,
                    metrics_before_flush=metrics_before_flush,
                    metrics_after_flush=metrics_after_flush,
                    flush_result=flush_result,
                )
                rows.append(row)

                log(
                    f"{label}: "
                    f"throughput={row['throughput_req_sec']} req/sec, "
                    f"avg_latency={row['avg_latency_ms']} ms, "
                    f"db_accesses={row['db_accesses']}, "
                    f"cache_hit_rate={row['cache_hit_rate']}, "
                    f"errors={row['errors']}"
                )
                if target_name == "write_back":
                    log(
                        f"write_back / {load_level.name} / {workload_name}: "
                        f"pending_before_flush={row['write_back_pending_before_flush']}, "
                        f"pending_max={row['write_back_pending_max']}, "
                        f"manual_flush={row['manual_flush_count']}"
                    )

    for line in format_results_table(rows):
        log(line)

    log(f"Results saved to {output_dir}")
    write_console_log(output_dir / "console-log.txt", logs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified cache strategy load generator")
    parser.add_argument(
        "--target",
        action="append",
        help="Strategy target in name=url format. Can be repeated.",
    )
    parser.add_argument("--requests", type=int, default=6600)
    parser.add_argument("--duration", type=float, default=12.0)
    parser.add_argument("--concurrency", type=int, default=72)
    parser.add_argument("--dataset-size", type=int, default=1000)
    parser.add_argument("--hot-set-size", type=int, default=50)
    parser.add_argument("--hot-key-ratio", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=20260429)
    parser.add_argument("--output-dir", default="results")
    return parser.parse_args()


def build_load_levels(args: argparse.Namespace) -> list[LoadLevel]:
    levels: list[LoadLevel] = []
    for name, config in LOAD_LEVELS.items():
        requests = max(1, math.ceil(args.requests * config["request_multiplier"]))
        concurrency = max(1, math.ceil(args.concurrency * config["concurrency_multiplier"]))
        target_rps = round(requests / args.duration, 2)
        levels.append(
            LoadLevel(
                name=name,
                requests=requests,
                duration=args.duration,
                concurrency=concurrency,
                target_rps=target_rps,
            )
        )
    return levels


def parse_targets(raw_targets: list[str]) -> dict[str, str]:
    targets: dict[str, str] = {}
    for raw in raw_targets:
        if "=" not in raw:
            raise ValueError(f"Target must use name=url format: {raw!r}")
        name, url = raw.split("=", 1)
        targets[name.strip()] = url.strip().rstrip("/")
    return targets


def build_operations(
    read_ratio: float,
    request_count: int,
    dataset_size: int,
    hot_set_size: int,
    hot_key_ratio: float,
    seed: int,
) -> list[Operation]:
    rng = random.Random(seed)
    operations: list[Operation] = []
    hot_limit = max(1, min(hot_set_size, dataset_size))
    for index in range(request_count):
        item_id = choose_item_id(rng, dataset_size, hot_limit, hot_key_ratio)
        if rng.random() < read_ratio:
            operations.append(Operation("GET", item_id))
        else:
            value = f"value-{seed}-{index}-{rng.randint(1000, 9999)}"
            operations.append(Operation("PUT", item_id, value=value))
    return operations


def choose_item_id(
    rng: random.Random,
    dataset_size: int,
    hot_limit: int,
    hot_key_ratio: float,
) -> int:
    if rng.random() < hot_key_ratio:
        return rng.randint(1, hot_limit)
    if hot_limit < dataset_size:
        return rng.randint(hot_limit + 1, dataset_size)
    return rng.randint(1, dataset_size)


def wait_for_health(base_url: str, log) -> None:
    deadline = time.monotonic() + 30
    last_error = ""
    while time.monotonic() < deadline:
        try:
            health = get_json(f"{base_url}/health", timeout=2)
            log(
                f"{base_url}: health ok "
                f"(strategy={health['strategy']}, cache={health['cache']})"
            )
            return
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            time.sleep(0.5)
    raise RuntimeError(f"{base_url} did not become healthy: {last_error}")


def run_workload(
    base_url: str,
    operations: list[Operation],
    duration_seconds: float,
    concurrency: int,
) -> dict:
    start = time.perf_counter()
    results: list[RequestResult] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        count = len(operations)
        for index, operation in enumerate(operations):
            due_at = start + (duration_seconds * index / max(count - 1, 1))
            sleep_for = due_at - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)
            futures.append(executor.submit(execute_operation, base_url, operation))

        for future in as_completed(futures):
            results.append(future.result())

    elapsed = time.perf_counter() - start
    latencies = [result.latency_ms for result in results if result.ok]
    errors = [result for result in results if not result.ok]
    return {
        "elapsed_seconds": elapsed,
        "success": len(latencies),
        "errors": len(errors),
        "avg_latency_ms": statistics.mean(latencies) if latencies else 0.0,
        "p95_latency_ms": percentile(latencies, 95) if latencies else 0.0,
        "throughput_req_sec": len(latencies) / elapsed if elapsed else 0.0,
    }


def execute_operation(base_url: str, operation: Operation) -> RequestResult:
    started = time.perf_counter()
    try:
        if operation.method == "GET":
            get_json(f"{base_url}/items/{operation.item_id}")
        else:
            put_json(
                f"{base_url}/items/{operation.item_id}",
                {"value": operation.value},
            )
        latency_ms = (time.perf_counter() - started) * 1000
        return RequestResult(ok=True, latency_ms=latency_ms, status=200)
    except error.HTTPError as exc:
        latency_ms = (time.perf_counter() - started) * 1000
        return RequestResult(ok=False, latency_ms=latency_ms, status=exc.code, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.perf_counter() - started) * 1000
        return RequestResult(ok=False, latency_ms=latency_ms, error=str(exc))


def build_result_row(
    target_name: str,
    load_level: LoadLevel,
    workload_name: str,
    generator_result: dict,
    metrics_before_flush: dict,
    metrics_after_flush: dict,
    flush_result: dict,
) -> dict:
    cache_metrics = metrics_before_flush["cache"]
    db = metrics_before_flush["db"]
    write_back_before = metrics_before_flush["write_back"]
    write_back_after = metrics_after_flush["write_back"]
    return {
        "strategy": target_name,
        "load": load_level.name,
        "target_rps": load_level.target_rps,
        "cache": metrics_before_flush.get("cache_name", "redis"),
        "workload": workload_name,
        "requests": load_level.requests,
        "target_duration_sec": load_level.duration,
        "concurrency": load_level.concurrency,
        "elapsed_sec": round(generator_result["elapsed_seconds"], 3),
        "throughput_req_sec": round(generator_result["throughput_req_sec"], 2),
        "avg_latency_ms": round(generator_result["avg_latency_ms"], 2),
        "p95_latency_ms": round(generator_result["p95_latency_ms"], 2),
        "errors": generator_result["errors"],
        "db_reads": db["reads"],
        "db_writes": db["writes"],
        "db_accesses": db["accesses"],
        "cache_hits": cache_metrics["hits"],
        "cache_misses": cache_metrics["misses"],
        "cache_hit_rate": cache_metrics["hit_rate"],
        "write_back_pending_before_flush": write_back_before["pending"],
        "write_back_pending_after_flush": write_back_after["pending"],
        "write_back_pending_max": write_back_before["pending_max"],
        "write_back_flushed_total": write_back_after["flushed"],
        "manual_flush_count": flush_result["flushed"],
    }


def get_json(url: str, timeout: float = 10) -> dict:
    with request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict, timeout: float = 20) -> dict:
    return send_json("POST", url, payload, timeout=timeout)


def put_json(url: str, payload: dict, timeout: float = 10) -> dict:
    return send_json("PUT", url, payload, timeout=timeout)


def send_json(method: str, url: str, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile_value / 100)
    return ordered[index]


def write_console_log(path: Path, logs: list[str]) -> None:
    path.write_text("\n".join(logs) + "\n", encoding="utf-8")


def format_results_table(rows: list[dict]) -> list[str]:
    if not rows:
        return ["No results"]

    headers = [
        "strategy",
        "load",
        "target_rps",
        "workload",
        "req/sec",
        "avg_ms",
        "p95_ms",
        "db_accesses",
        "cache_hit_rate",
        "wb_pending_max",
        "errors",
    ]
    values = [
        [
            row["strategy"],
            row["load"],
            row["target_rps"],
            row["workload"],
            row["throughput_req_sec"],
            row["avg_latency_ms"],
            row["p95_latency_ms"],
            row["db_accesses"],
            row["cache_hit_rate"],
            row["write_back_pending_max"],
            row["errors"],
        ]
        for row in rows
    ]
    widths = [
        max(len(str(header)), *(len(str(value[index])) for value in values))
        for index, header in enumerate(headers)
    ]

    def render_row(row_values: list[object]) -> str:
        return " | ".join(
            str(value).ljust(widths[index])
            for index, value in enumerate(row_values)
        )

    separator = "-+-".join("-" * width for width in widths)
    return [
        "",
        "RESULT TABLE",
        render_row(headers),
        separator,
        *(render_row(row) for row in values),
    ]


def format_load_level_summary(args: argparse.Namespace) -> str:
    parts = []
    for level in build_load_levels(args):
        parts.append(
            f"`{level.name}` {level.target_rps} req/sec "
            f"({level.requests} requests, concurrency {level.concurrency})"
        )
    return ", ".join(parts)


def format_workload_summary() -> str:
    parts = []
    for name, read_ratio in WORKLOADS.items():
        read_percent = round(read_ratio * 100)
        write_percent = 100 - read_percent
        parts.append(f"`{name}` {read_percent}/{write_percent}")
    return ", ".join(parts)

if __name__ == "__main__":
    main()
