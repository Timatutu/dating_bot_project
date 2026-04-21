from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime

from rich.console import Console
from rich.table import Table
from tabulate import tabulate

from bench import JsonResultRepository, run_matrix, settings
from bench.readiness import wait_for_brokers
from bench.scenarios import (
    DEFAULT_RATES,
    DEFAULT_SIZES,
    TZ_EXPERIMENT_BASELINE,
    TZ_EXPERIMENT_RATE,
    TZ_EXPERIMENT_SIZE,
)

console = Console()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Три эксперимента из ТЗ: baseline, размер сообщения, интенсивность.")
    p.add_argument("--duration", type=float, default=10.0, help="Минимальная/основная длительность прогона (сек)")
    p.add_argument(
        "--messages",
        type=int,
        default=None,
        help="Остановиться после стольких отправок на прогон (ТЗ: объём вместо времени; время — потолок)",
    )
    p.add_argument("--drain", type=float, default=5.0, help="Секунд добора очереди после продюсеров")
    return p.parse_args()


def _rich(title: str, rows: list[dict]) -> None:
    t = Table(title=title)
    for c in ["broker", "rate", "size", "sent", "recv", "lost", "eff/s", "avg ms", "p95 ms", "max ms"]:
        t.add_column(c, justify="right")
    for r in rows:
        cfg = r["config"]
        t.add_row(
            cfg["broker"], str(cfg["target_rate"]), str(cfg["message_size"]),
            str(r["sent"]), str(r["received"]), str(r["lost"]),
            str(r["effective_msg_per_sec"]),
            str(r["latency_avg_ms"]), str(r["latency_p95_ms"]), str(r["latency_max_ms"]),
        )
    console.print(t)


def _md_table(rows: list[dict]) -> str:
    cols = ["broker", "rate", "size(B)", "sent", "recv", "lost", "errors",
            "eff/s", "avg ms", "p95 ms", "max ms"]
    data = [[
        r["config"]["broker"], r["config"]["target_rate"], r["config"]["message_size"],
        r["sent"], r["received"], r["lost"], r["errors"],
        r["effective_msg_per_sec"], r["latency_avg_ms"], r["latency_p95_ms"], r["latency_max_ms"],
    ] for r in rows]
    return tabulate(data, headers=cols, tablefmt="github")


async def main() -> None:
    args = _parse_args()
    repo = JsonResultRepository(settings.results_dir)

    console.print("[dim]waiting for RabbitMQ + Redis…[/dim]")
    await wait_for_brokers(settings)

    console.rule("[bold]running matrix (ТЗ)")
    console.print(
        f"[dim]{TZ_EXPERIMENT_BASELINE}: одинаковая нагрузка rabbitmq/redis | "
        f"{TZ_EXPERIMENT_SIZE}: размеры {list(DEFAULT_SIZES)} B | "
        f"{TZ_EXPERIMENT_RATE}: rates {list(DEFAULT_RATES)} msg/s[/dim]",
    )
    report = await run_matrix(
        duration=args.duration,
        drain_seconds=args.drain,
        target_messages=args.messages,
        settings_=settings,
        sink=None,
        repo=repo,
    )
    console.print(f"[dim]режим нагрузки: {json.dumps(report['tz_load'], ensure_ascii=False)}[/dim]")

    _rich("1. Базовое сравнение (ТЗ)", report["baseline"])
    _rich("2. Влияние размера сообщения (ТЗ)", report["message_size_sweep"])
    _rich("3. Влияние интенсивности потока (ТЗ)", report["rate_ramp"])

    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    md_path = repo.dir / f"matrix_{stamp}.md"
    md_path.write_text(
        "\n\n".join([
            f"# Broker benchmark matrix — {report['generated_at']}",
            "## Параметры ТЗ (нагрузка)",
            "```json",
            json.dumps(report["tz_load"], indent=2, ensure_ascii=False),
            "```",
            "## 1. Базовое сравнение",
            _md_table(report["baseline"]),
            "## 2. Влияние размера сообщения",
            _md_table(report["message_size_sweep"]),
            "## 3. Влияние интенсивности потока",
            _md_table(report["rate_ramp"]),
        ]),
        encoding="utf-8",
    )
    console.print(f"[green]markdown report: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
