from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, Request

from .cache import RedisCache
from .config import Settings, get_settings
from .database import Database
from .metrics import Metrics
from .schemas import ItemOut, ItemWrite, ResetRequest
from .strategies import WriteBackStrategy, build_strategy


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database = Database(settings.database_url, settings.db_schema)
    database.initialize()

    cache = RedisCache(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        prefix=settings.cache_prefix,
    )
    metrics = Metrics()
    strategy = build_strategy(settings.cache_strategy, cache, database, metrics)

    if database.count_items() == 0:
        database.reset(settings.startup_seed_size)
        cache.clear()

    app.state.settings = settings
    app.state.database = database
    app.state.cache = cache
    app.state.metrics = metrics
    app.state.strategy = strategy
    app.state.write_back_task = None

    if isinstance(strategy, WriteBackStrategy):
        app.state.write_back_task = asyncio.create_task(
            strategy.flush_forever(
                settings.write_back_flush_interval,
                settings.write_back_batch_size,
            )
        )

    try:
        yield
    finally:
        task = app.state.write_back_task
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="Cache Strategy Comparison",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health(request: Request) -> dict:
    settings: Settings = request.app.state.settings
    request.app.state.cache.ping()
    request.app.state.database.ping()
    return {
        "status": "ok",
        "strategy": settings.cache_strategy,
        "cache": "redis",
        "database": "postgresql",
        "db_schema": settings.db_schema,
    }


@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, request: Request) -> dict:
    try:
        return request.app.state.strategy.read(item_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Item not found") from exc


@app.put("/items/{item_id}", response_model=ItemOut)
def put_item(item_id: int, body: ItemWrite, request: Request) -> dict:
    return request.app.state.strategy.write(item_id, body.value)


@app.get("/metrics")
def metrics(request: Request) -> dict:
    settings: Settings = request.app.state.settings
    strategy = request.app.state.strategy
    pending = strategy.pending_dirty_writes()
    return {
        "strategy": settings.cache_strategy,
        "cache_name": "redis",
        **request.app.state.metrics.snapshot(pending_dirty_writes=pending),
    }


@app.post("/admin/reset")
def reset(body: ResetRequest, request: Request) -> dict:
    request.app.state.cache.clear()
    request.app.state.database.reset(body.dataset_size)
    request.app.state.metrics.reset()
    return {
        "status": "reset",
        "dataset_size": body.dataset_size,
        "strategy": request.app.state.settings.cache_strategy,
    }


@app.post("/admin/flush")
def flush_write_back(request: Request) -> dict:
    strategy = request.app.state.strategy
    flushed = strategy.flush()
    return {
        "flushed": flushed,
        "pending": strategy.pending_dirty_writes(),
        "strategy": request.app.state.settings.cache_strategy,
    }
