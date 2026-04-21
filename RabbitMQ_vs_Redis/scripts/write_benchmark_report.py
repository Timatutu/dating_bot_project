from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from bench import BenchmarkConfig, BenchmarkResult, settings


def _latest(dir_path: Path, pattern: str) -> Path | None:
    files = sorted(dir_path.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _result_from_row(d: dict) -> BenchmarkResult:
    c = d["config"]
    cfg = BenchmarkConfig(
        broker=c["broker"],
        target_rate=c["target_rate"],
        message_size=c["message_size"],
        duration=c["duration"],
        producers=c.get("producers", 1),
        consumers=c.get("consumers", 1),
        drain_seconds=c.get("drain_seconds", 5.0),
        target_messages=c.get("target_messages"),
    )
    return BenchmarkResult(
        config=cfg,
        duration_sec=d["duration_sec"],
        sent=d["sent"],
        received=d["received"],
        lost=d["lost"],
        errors=d["errors"],
        effective_msg_per_sec=d["effective_msg_per_sec"],
        latency_avg_ms=d["latency_avg_ms"],
        latency_p95_ms=d["latency_p95_ms"],
        latency_max_ms=d["latency_max_ms"],
        timestamp=d["timestamp"],
    )


def _fmt_row(r: BenchmarkResult) -> str:
    deg, why = r.is_degraded()
    flag = "⚠ деградация" if deg else "ok"
    return (
        f"| {r.config.broker} | {r.config.target_rate} | {r.config.message_size} | "
        f"{r.effective_msg_per_sec:.1f} | {r.latency_p95_ms:.2f} | {r.lost} | {flag}: {why} |"
    )


def _section_matrix(data: dict) -> str:
    lines = [
        "## Матрица ТЗ",
        f"Сгенерировано (файл): `{data.get('generated_at', '')}`",
        "",
        "### 1. Базовое сравнение",
        "| broker | rate | size(B) | eff/s | p95 ms | lost | критерии |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in data.get("baseline", []):
        lines.append(_fmt_row(_result_from_row(row)))
    lines += [
        "",
        "### 2. Влияние размера сообщения",
        "| broker | rate | size(B) | eff/s | p95 ms | lost | критерии |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in data.get("message_size_sweep", []):
        lines.append(_fmt_row(_result_from_row(row)))
    lines += [
        "",
        "### 3. Интенсивность потока (rate ramp)",
        "| broker | rate | size(B) | eff/s | p95 ms | lost | критерии |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in data.get("rate_ramp", []):
        lines.append(_fmt_row(_result_from_row(row)))
    if "tz_load" in data:
        lines += ["", "### Параметры нагрузки (tz_load)", "```json", json.dumps(data["tz_load"], indent=2, ensure_ascii=False), "```"]
    return "\n".join(lines)


def _section_breaking(data: dict) -> str:
    lines = [
        "## Точка деградации (breaking point)",
        f"Время: `{data.get('generated_at', '')}`",
        "",
        "Критерии деградации (как в коде): eff/s < 85% от target; потери > 5% от sent; p95 > 500 ms.",
        "",
    ]
    for bp in data.get("per_broker", []):
        broker = bp["broker"]
        at = bp.get("degraded_at")
        lines.append(f"### {broker}")
        lines.append(f"- **Первый target с деградацией:** {at if at is not None else 'нет (все шаги ok)'}")
        lines.append("")
        lines.append("| target | eff/s | p95 ms | lost | sent | вердикт |")
        lines.append("|---:|---:|---:|---:|---:|---|")
        for raw in bp.get("runs", []):
            r = _result_from_row(raw)
            deg, why = r.is_degraded()
            lines.append(
                f"| {r.config.target_rate} | {r.effective_msg_per_sec} | {r.latency_p95_ms} | "
                f"{r.lost} | {r.sent} | {why} |",
            )
        lines.append("")
    return "\n".join(lines)


def _auto_observations(matrix: dict) -> str:
    lines: list[str] = ["## Автоматические наблюдения по матрице", ""]
    baseline = matrix.get("baseline") or []
    by_b = {r["config"]["broker"]: r for r in baseline}
    if len(by_b) == 2:
        rb, rr = by_b.get("rabbitmq"), by_b.get("redis")
        if rb and rr:
            lines.append(
                f"- **База (1k msg/s, 1 KiB):** Rabbit p95 **{rb['latency_p95_ms']} ms**, Redis p95 **{rr['latency_p95_ms']} ms** "
                f"(eff {rb['effective_msg_per_sec']} vs {rr['effective_msg_per_sec']} msg/s).",
            )
    ramp = matrix.get("rate_ramp") or []
    hi_rabbit = [r for r in ramp if r["config"]["broker"] == "rabbitmq"]
    hi_redis = [r for r in ramp if r["config"]["broker"] == "redis"]
    if hi_rabbit and hi_redis:
        last_r, last_d = hi_rabbit[-1], hi_redis[-1]
        rres, dres = _result_from_row(last_r), _result_from_row(last_d)
        rd, _ = rres.is_degraded()
        dd, _ = dres.is_degraded()
        lines.append(
            f"- **Максимальный шаг rate ramp** ({rres.config.target_rate} msg/s): Rabbit eff **{rres.effective_msg_per_sec}**, "
            f"p95 **{rres.latency_p95_ms} ms**, потери **{rres.lost}** — {'деградация по порогам' if rd else 'в пределах порогов'}; "
            f"Redis eff **{dres.effective_msg_per_sec}**, p95 **{dres.latency_p95_ms} ms**, потери **{dres.lost}** — "
            f"{'деградация по порогам' if dd else 'в пределах порогов'}.",
        )
    sweep = matrix.get("message_size_sweep") or []
    max_size = max((r["config"]["message_size"] for r in sweep), default=0)
    big = [r for r in sweep if r["config"]["message_size"] == max_size]
    for row in big:
        r = _result_from_row(row)
        deg, why = r.is_degraded()
        mark = f"({why})" if deg else "(ok)"
        lines.append(
            f"- **Большое сообщение ({max_size} B), {r.config.broker}:** eff **{r.effective_msg_per_sec}**, p95 **{r.latency_p95_ms} ms** {mark}.",
        )
    lines.append("")
    return "\n".join(lines)


def _section_quota(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = [
        "## Сценарий: квота сообщений",
        f"Файл: `{path.name}`",
        "",
        f"- Сообщений: {data.get('target_messages')}, целевой rate: {data.get('target_rate')}, drain: {data.get('drain_seconds')} s",
        "",
        "| broker | eff/s | p95 ms | lost | sent | recv |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in data.get("results", []):
        r = _result_from_row(row)
        lines.append(
            f"| {r.config.broker} | {r.effective_msg_per_sec} | {r.latency_p95_ms} | "
            f"{r.lost} | {r.sent} | {r.received} |",
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", type=Path, default=None)
    ap.add_argument("--breaking", type=Path, default=None)
    ap.add_argument("--quota", type=Path, default=None)
    ap.add_argument("-o", "--output", type=Path, default=None)
    args = ap.parse_args()

    rdir = settings.results_dir
    mpath = args.matrix or _latest(rdir, "matrix_*.json")
    bpath = args.breaking or _latest(rdir, "breaking_point_*.json")
    qpath = args.quota or _latest(rdir, "scenario_quota_*.json")
    out = args.output or (rdir / "BENCHMARK_REPORT.md")

    chunks = [
        "# Отчёт по метрикам бенчмарка",
        f"Сборка отчёта: `{datetime.utcnow().isoformat()}Z` (UTC).",
        "",
    ]

    if mpath and mpath.is_file():
        mdata = json.loads(mpath.read_text(encoding="utf-8"))
        chunks.append(_section_matrix(mdata))
        chunks.append(_auto_observations(mdata))
    else:
        chunks.append("*Файл matrix_*.json не найден — запусти `uv run python scripts/run_matrix.py`.*\n")

    if bpath and bpath.is_file():
        chunks.append(_section_breaking(json.loads(bpath.read_text(encoding="utf-8"))))
        chunks.append("")
    else:
        chunks.append("*Файл breaking_point_*.json не найден.*\n")

    if qpath and qpath.is_file():
        chunks.append(_section_quota(qpath))
        chunks.append("")


    out.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
