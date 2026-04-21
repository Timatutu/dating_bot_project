from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime

from rich.console import Console

from bench import (
    BenchmarkConfig,
    JsonResultRepository,
    duration_for_message_quota,
    find_breaking_point,
    run_benchmark,
    run_matrix,
    settings,
)
from bench.readiness import wait_for_brokers

console = Console()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Сценарии: matrix | breaking | quota")
    p.add_argument(
        "--only",
        type=str,
        default="matrix,breaking,quota",
        help="Через запятую: matrix, breaking, quota (по умолчанию все)",
    )
    p.add_argument("--duration", type=float, default=10.0, help="Базовая длительность для matrix")
    p.add_argument("--drain", type=float, default=5.0, help="Drain после продюсеров (matrix)")
    p.add_argument("--quota-messages", type=int, default=50_000, help="Сценарий quota: всего сообщений")
    p.add_argument("--quota-rate", type=int, default=2_000, help="Сценарий quota: целевой msg/s")
    return p.parse_args()


async def _scenario_quota(
    *,
    repo: JsonResultRepository,
    messages: int,
    rate: int,
    drain: float,
) -> None:
    rows: list = []
    for broker in ("rabbitmq", "redis"):
        dur = duration_for_message_quota(rate, messages, drain_seconds=drain)
        cfg = BenchmarkConfig(
            broker=broker,
            target_rate=rate,
            message_size=1_024,
            duration=dur,
            drain_seconds=drain,
            target_messages=messages,
        )
        console.print(f"[bold]quota[/bold] {broker} {messages} msgs @ {rate}/s (cap {dur:.0f}s)")
        r = await run_benchmark(cfg, settings, None, repo)
        rows.append(asdict(r))
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    repo.save_report(
        f"scenario_quota_{stamp}.json",
        {
            "generated_at": datetime.utcnow().isoformat(),
            "scenario": "message_quota",
            "target_messages": messages,
            "target_rate": rate,
            "drain_seconds": drain,
            "results": rows,
        },
    )
    console.print(f"[green]scenario_quota → results/scenario_quota_{stamp}.json")


async def main() -> None:
    args = _parse_args()
    parts = {x.strip().lower() for x in args.only.split(",") if x.strip()}

    repo = JsonResultRepository(settings.results_dir)

    console.print("[dim]waiting for RabbitMQ + Redis…[/dim]")
    await wait_for_brokers(settings)

    if "matrix" in parts:
        console.rule("[bold]scenario: matrix (ТЗ)")
        await run_matrix(
            duration=args.duration,
            drain_seconds=args.drain,
            settings_=settings,
            sink=None,
            repo=repo,
        )
    if "breaking" in parts:
        console.rule("[bold]scenario: breaking point")
        await find_breaking_point(settings_=settings, sink=None, repo=repo)
    if "quota" in parts:
        console.rule("[bold]scenario: message quota")
        await _scenario_quota(
            repo=repo,
            messages=args.quota_messages,
            rate=args.quota_rate,
            drain=max(args.drain, 5.0),
        )


if __name__ == "__main__":
    asyncio.run(main())
