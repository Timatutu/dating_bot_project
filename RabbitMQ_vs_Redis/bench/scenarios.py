from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from bench.core import (
    BenchmarkConfig,
    BenchmarkResult,
    JsonResultRepository,
    Settings,
    run_benchmark,
    settings as default_settings,
)

DEFAULT_BROKERS: tuple[str, ...] = ("rabbitmq", "redis")
DEFAULT_SIZES: tuple[int, ...] = (128, 1_024, 10_240, 102_400)
DEFAULT_RATES: tuple[int, ...] = (1_000, 5_000, 10_000)
DEFAULT_RATE_STEPS: tuple[int, ...] = (
    1_000, 2_500, 5_000, 7_500, 10_000, 15_000, 20_000, 30_000, 50_000,
)

TZ_EXPERIMENT_BASELINE = "1_базовое_сравнение"
TZ_EXPERIMENT_SIZE = "2_влияние_размера_сообщения"
TZ_EXPERIMENT_RATE = "3_влияние_интенсивности_потока"


def duration_for_message_quota(
    target_rate: int,
    target_messages: int,
    *,
    drain_seconds: float,
    floor_seconds: float = 10.0,
) -> float:
    r = max(target_rate, 1)
    return max(floor_seconds, target_messages / r * 1.8 + drain_seconds + 5.0)


async def run_matrix(
    *,
    duration: float = 10.0,
    target_messages: int | None = None,
    drain_seconds: float = 5.0,
    brokers: tuple[str, ...] = DEFAULT_BROKERS,
    sizes: tuple[int, ...] = DEFAULT_SIZES,
    rates: tuple[int, ...] = DEFAULT_RATES,
    settings_: Settings | None = None,
    sink: Any | None = None,
    repo: JsonResultRepository | None = None,
) -> dict:
    """Три эксперимента из ТЗ: baseline + sweep по размерам + ramp по rate.

    Режим нагрузки (как в ТЗ):
    - только ``duration`` — ограничение по времени;
    - ``target_messages`` — ограничение по **числу отправленных** сообщений; ``duration`` тогда
      используется как минимальный потолок, а фактический потолок считается под каждый ``target_rate``.
    """
    s = settings_ or default_settings

    def eff_duration(for_rate: int) -> float:
        if target_messages is None:
            return duration
        return max(
            duration,
            duration_for_message_quota(for_rate, target_messages, drain_seconds=drain_seconds),
        )

    baseline: list[BenchmarkResult] = [
        await run_benchmark(
            BenchmarkConfig(
                broker=b,
                target_rate=1_000,
                message_size=1_024,
                duration=eff_duration(1_000),
                drain_seconds=drain_seconds,
                target_messages=target_messages,
            ),
            s, sink, repo,
        )
        for b in brokers
    ]
    size_sweep: list[BenchmarkResult] = [
        await run_benchmark(
            BenchmarkConfig(
                broker=b,
                target_rate=1_000,
                message_size=sz,
                duration=eff_duration(1_000),
                drain_seconds=drain_seconds,
                target_messages=target_messages,
            ),
            s, sink, repo,
        )
        for b in brokers for sz in sizes
    ]
    rate_ramp: list[BenchmarkResult] = [
        await run_benchmark(
            BenchmarkConfig(
                broker=b,
                target_rate=r,
                message_size=1_024,
                duration=eff_duration(r),
                drain_seconds=drain_seconds,
                target_messages=target_messages,
            ),
            s, sink, repo,
        )
        for b in brokers for r in rates
    ]

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "tz_load": {
            "mode": "messages" if target_messages is not None else "duration",
            "duration_floor_sec": duration,
            "target_messages": target_messages,
            "drain_seconds": drain_seconds,
            "sizes_bytes": list(sizes),
            "rates_msg_per_sec": list(rates),
        },
        "baseline": [asdict(r) for r in baseline],
        "message_size_sweep": [asdict(r) for r in size_sweep],
        "rate_ramp": [asdict(r) for r in rate_ramp],
    }
    if repo is not None:
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        repo.save_report(f"matrix_{stamp}.json", report)
    return report


async def find_breaking_point(
    *,
    brokers: tuple[str, ...] = DEFAULT_BROKERS,
    rate_steps: tuple[int, ...] = DEFAULT_RATE_STEPS,
    message_size: int = 1_024,
    duration: float = 10.0,
    drain_seconds: float = 10.0,
    settings_: Settings | None = None,
    sink: Any | None = None,
    repo: JsonResultRepository | None = None,
) -> dict:
    s = settings_ or default_settings
    per_broker: list[dict] = []

    for broker in brokers:
        runs: list[BenchmarkResult] = []
        degraded_at: int | None = None
        for rate in rate_steps:
            result = await run_benchmark(
                BenchmarkConfig(
                    broker=broker,
                    target_rate=rate,
                    message_size=message_size,
                    duration=duration,
                    drain_seconds=drain_seconds,
                ),
                s, sink, repo,
            )
            runs.append(result)
            degraded, _ = result.is_degraded()
            if degraded:
                degraded_at = rate
                break
        per_broker.append({
            "broker": broker,
            "degraded_at": degraded_at,
            "runs": [asdict(r) for r in runs],
        })

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "per_broker": per_broker,
    }
    if repo is not None:
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        repo.save_report(f"breaking_point_{stamp}.json", report)
    return report
