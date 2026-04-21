from __future__ import annotations

import asyncio
import json
import os
import struct
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Protocol

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_queue: str = "bench"

    redis_url: str = "redis://localhost:6379/0"
    redis_stream: str = "bench-stream"
    redis_group: str = "bench-group"
    redis_consumer: str = "bench-consumer"

    results_dir: Path = Path(__file__).resolve().parents[1] / "results"


settings = Settings()

HEADER = struct.Struct("<Qd")


def encode(seq: int, size: int) -> bytes:
    head = HEADER.pack(seq, time.time())
    if size <= HEADER.size:
        return head[:size]
    return head + os.urandom(size - HEADER.size)


def decode(payload: bytes) -> tuple[int, float]:
    seq, ts = HEADER.unpack_from(payload, 0)
    return seq, ts

@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    broker: str
    target_rate: int
    message_size: int
    duration: float
    producers: int = 1
    consumers: int = 1
    drain_seconds: float = 5.0
    target_messages: int | None = None


@dataclass(slots=True)
class BenchmarkMetrics:
    config: BenchmarkConfig
    sent: int = 0
    received: int = 0
    errors: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    started_at: float = field(default_factory=time.monotonic)
    ended_at: float | None = None

    def mark_sent(self) -> None:
        self.sent += 1

    def mark_error(self) -> None:
        self.errors += 1

    def mark_received(self, latency_ms: float) -> None:
        self.received += 1
        self.latencies_ms.append(latency_ms)

    def finalize(self) -> BenchmarkResult:
        self.ended_at = time.monotonic()
        elapsed = self.ended_at - self.started_at
        sorted_lat = sorted(self.latencies_ms)

        def pct(p: float) -> float:
            if not sorted_lat:
                return 0.0
            idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * p))
            return sorted_lat[idx]

        return BenchmarkResult(
            config=self.config,
            duration_sec=round(elapsed, 2),
            sent=self.sent,
            received=self.received,
            lost=max(self.sent - self.received, 0),
            errors=self.errors,
            effective_msg_per_sec=round(self.received / elapsed, 1) if elapsed else 0.0,
            latency_avg_ms=round(mean(self.latencies_ms), 2) if self.latencies_ms else 0.0,
            latency_p95_ms=round(pct(0.95), 2),
            latency_max_ms=round(max(self.latencies_ms), 2) if self.latencies_ms else 0.0,
            timestamp=datetime.utcnow().isoformat(),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    config: BenchmarkConfig
    duration_sec: float
    sent: int
    received: int
    lost: int
    errors: int
    effective_msg_per_sec: float
    latency_avg_ms: float
    latency_p95_ms: float
    latency_max_ms: float
    timestamp: str

    def is_degraded(
        self,
        min_effective_ratio: float = 0.85,
        max_loss_ratio: float = 0.05,
        max_p95_ms: float = 500.0,
    ) -> tuple[bool, str]:
        target = self.config.target_rate
        if self.effective_msg_per_sec < target * min_effective_ratio:
            return True, f"throughput {self.effective_msg_per_sec:.0f}/s < {min_effective_ratio:.0%} of {target}/s"
        sent = self.sent or 1
        if self.lost / sent > max_loss_ratio:
            return True, f"lost {self.lost}/{sent} = {self.lost / sent:.1%}"
        if self.latency_p95_ms > max_p95_ms:
            return True, f"p95 {self.latency_p95_ms}ms > {max_p95_ms}ms"
        return False, "ok"



class Broker(Protocol):
    name: str

    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def reset(self) -> None: ...
    async def publish(self, payload: bytes) -> None: ...
    def consume(self): ...  



class JsonResultRepository:
    def __init__(self, results_dir: Path) -> None:
        self._dir = results_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def dir(self) -> Path:
        return self._dir

    def save(self, result: BenchmarkResult) -> None:
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        name = (
            f"{stamp}_{result.config.broker}"
            f"_{result.config.target_rate}rps"
            f"_{result.config.message_size}b.json"
        )
        (self._dir / name).write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")

    def save_report(self, name: str, payload: dict) -> str:
        path = self._dir / name
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)

    def list_all(self) -> list[dict]:
        out: list[dict] = []
        for p in sorted(self._dir.glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out

async def run_benchmark(
    config: BenchmarkConfig,
    settings_: Settings | None = None,
    sink: Any | None = None,
    repo: JsonResultRepository | None = None,
) -> BenchmarkResult:
    from bench.brokers import make_broker

    broker = make_broker(config.broker, settings_ or settings)
    await broker.connect()
    if sink is not None:
        sink.on_started(config)
    try:
        await broker.reset()
        metrics = BenchmarkMetrics(config=config)
        await _drive(broker, config, metrics, sink)
        result = metrics.finalize()
    finally:
        await broker.close()

    if sink is not None:
        sink.on_finished(result)
    if repo is not None:
        repo.save(result)
    return result


async def _drive(
    broker: Broker,
    config: BenchmarkConfig,
    metrics: BenchmarkMetrics,
    sink: Any | None,
) -> None:
    stop_consumers = asyncio.Event()
    per_producer_rate = max(1, config.target_rate // config.producers)

    producers = [
        asyncio.create_task(
            _produce(broker, per_producer_rate, config, metrics, sink, producer_idx=i),
        )
        for i in range(config.producers)
    ]
    consumers = [
        asyncio.create_task(_consume(broker, config, metrics, sink, stop_consumers))
        for _ in range(config.consumers)
    ]

    await asyncio.gather(*producers)
    await _drain(metrics, config.drain_seconds)

    stop_consumers.set()
    for c in consumers:
        c.cancel()
    await asyncio.gather(*consumers, return_exceptions=True)


async def _produce(
    broker: Broker,
    rate: int,
    config: BenchmarkConfig,
    metrics: BenchmarkMetrics,
    sink: Any | None,
    producer_idx: int = 0,
) -> None:
    interval = 1.0 / rate if rate > 0 else 0.0
    deadline = time.monotonic() + config.duration
    next_send = time.monotonic()
    seq = 0
    local_quota: int | None = None
    local_sent = 0
    if config.target_messages is not None:
        n = config.producers
        base = config.target_messages // n
        rem = config.target_messages % n
        local_quota = base + (1 if producer_idx < rem else 0)
    while True:
        if time.monotonic() >= deadline:
            break
        if local_quota is not None and local_sent >= local_quota:
            break
        try:
            await broker.publish(encode(seq, config.message_size))
            metrics.mark_sent()
            local_sent += 1
            if sink is not None:
                sink.on_sent(config.broker)
            seq += 1
        except Exception:
            metrics.mark_error()
            if sink is not None:
                sink.on_error(config.broker)
        next_send += interval
        sleep_for = next_send - time.monotonic()
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)


async def _consume(
    broker: Broker,
    config: BenchmarkConfig,
    metrics: BenchmarkMetrics,
    sink: Any | None,
    stop: asyncio.Event,
) -> None:
    try:
        async for body in broker.consume():
            try:
                _, sent_ts = decode(body)
                latency_ms = (time.time() - sent_ts) * 1000.0
                metrics.mark_received(latency_ms)
                if sink is not None:
                    sink.on_received(config.broker, latency_ms)
            except Exception:
                metrics.mark_error()
                if sink is not None:
                    sink.on_error(config.broker)
            if stop.is_set():
                break
    except asyncio.CancelledError:
        pass


async def _drain(metrics: BenchmarkMetrics, drain_seconds: float) -> None:
    deadline = time.monotonic() + drain_seconds
    while time.monotonic() < deadline:
        if metrics.received >= metrics.sent:
            return
        await asyncio.sleep(0.2)
