from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from bench.core import (
    BenchmarkConfig,
    JsonResultRepository,
    run_benchmark,
    settings,
)
from bench.scenarios import find_breaking_point, run_matrix

repo = JsonResultRepository(settings.results_dir)

app = FastAPI(
    title="broker-bench",
    version="0.2.0",
    description="RabbitMQ vs Redis single-instance benchmark",
)


class RunRequest(BaseModel):
    broker: Literal["rabbitmq", "redis"]
    target_rate: int = Field(1_000, gt=0)
    message_size: int = Field(128, ge=16)
    duration: float = Field(10.0, gt=0)
    producers: int = Field(1, ge=1)
    consumers: int = Field(1, ge=1)
    drain_seconds: float = Field(5.0, ge=0)
    target_messages: int | None = Field(
        None,
        gt=0,
        description="ТЗ: остановиться после N отправок; duration — потолок по времени",
    )


class MatrixRequest(BaseModel):
    duration: float = Field(10.0, gt=0)
    drain_seconds: float = Field(5.0, ge=0)
    target_messages: int | None = Field(None, gt=0)


class BreakingPointRequest(BaseModel):
    message_size: int = Field(1_024, ge=16)
    duration: float = Field(10.0, gt=0)
    drain_seconds: float = Field(10.0, ge=0)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/bench/run")
async def bench_run(req: RunRequest) -> dict:
    config = BenchmarkConfig(**req.model_dump())
    result = await run_benchmark(config, settings, None, repo)
    return asdict(result)


@app.post("/bench/matrix")
async def bench_matrix(req: MatrixRequest) -> dict:
    return await run_matrix(
        duration=req.duration,
        drain_seconds=req.drain_seconds,
        target_messages=req.target_messages,
        settings_=settings,
        sink=None,
        repo=repo,
    )


@app.post("/bench/breaking-point")
async def bench_breaking_point(req: BreakingPointRequest) -> dict:
    return await find_breaking_point(
        message_size=req.message_size,
        duration=req.duration,
        drain_seconds=req.drain_seconds,
        settings_=settings,
        sink=None,
        repo=repo,
    )


@app.get("/results")
async def list_results() -> list[dict]:
    return repo.list_all()
