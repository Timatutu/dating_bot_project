from __future__ import annotations

import asyncio

from rich.console import Console
from rich.table import Table

from bench import (
    BenchmarkConfig,
    BenchmarkResult,
    JsonResultRepository,
    find_breaking_point,
    settings,
)
from bench.readiness import wait_for_brokers

console = Console()


def _result_from_dict(d: dict) -> BenchmarkResult:
    cfg = BenchmarkConfig(**d["config"])
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


async def main() -> None:
    repo = JsonResultRepository(settings.results_dir)

    console.print("[dim]waiting for RabbitMQ + Redis…[/dim]")
    await wait_for_brokers(settings)

    report = await find_breaking_point(settings_=settings, sink=None, repo=repo)

    for bp in report["per_broker"]:
        broker = bp["broker"]
        t = Table(title=f"{broker} — breaking-point scan")
        for c in ["target", "eff/s", "sent", "recv", "lost", "p95 ms", "verdict"]:
            t.add_column(c, justify="right")
        for raw in bp["runs"]:
            r = _result_from_dict(raw)
            deg, why = r.is_degraded()
            t.add_row(
                str(r.config.target_rate), str(r.effective_msg_per_sec),
                str(r.sent), str(r.received), str(r.lost),
                str(r.latency_p95_ms),
                ("[red]" + why) if deg else ("[green]" + why),
            )
        console.print(t)
        if bp["degraded_at"] is not None:
            console.print(f"[yellow]{broker} breaking point: {bp['degraded_at']} msg/s")
        else:
            console.print(f"[green]{broker} sustained top step without degrading")


if __name__ == "__main__":
    asyncio.run(main())
