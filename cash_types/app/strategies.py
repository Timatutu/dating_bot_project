from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import json
import time
from threading import Lock

from .cache import RedisCache
from .database import Database
from .metrics import Metrics


DIRTY_SET_KEY = "write_back_dirty_items"


class CacheStrategy(ABC):
    def __init__(self, cache: RedisCache, db: Database, metrics: Metrics) -> None:
        self.cache = cache
        self.db = db
        self.metrics = metrics

    def read(self, item_id: int) -> dict:
        self.metrics.read_request()
        cached = self.cache.get(_item_key(item_id))
        if cached is not None:
            self.metrics.cache_hit()
            return _decode_item(cached)

        self.metrics.cache_miss()
        self.metrics.db_read()
        item = self.db.get_item(item_id)
        if item is None:
            raise KeyError(item_id)
        self.cache.set(_item_key(item_id), _encode_item(item))
        return item

    @abstractmethod
    def write(self, item_id: int, value: str) -> dict:
        raise NotImplementedError

    def flush(self) -> int:
        return 0

    def pending_dirty_writes(self) -> int:
        return 0


class CacheAsideStrategy(CacheStrategy):
    def write(self, item_id: int, value: str) -> dict:
        self.metrics.write_request()
        item = self.db.upsert_item(item_id, value)
        self.metrics.db_write()
        self.cache.delete(_item_key(item_id))
        return item


class WriteThroughStrategy(CacheStrategy):
    def write(self, item_id: int, value: str) -> dict:
        self.metrics.write_request()
        item = self.db.upsert_item(item_id, value)
        self.metrics.db_write()
        self.cache.set(_item_key(item_id), _encode_item(item))
        return item


class WriteBackStrategy(CacheStrategy):
    def __init__(self, cache: RedisCache, db: Database, metrics: Metrics) -> None:
        super().__init__(cache, db, metrics)
        self._flush_lock = Lock()

    def write(self, item_id: int, value: str) -> dict:
        self.metrics.write_request()
        item = {
            "id": item_id,
            "name": f"Item {item_id}",
            "value": value,
            "updated_at": time.time(),
        }
        with self._flush_lock:
            self.cache.set(_item_key(item_id), _encode_item(item))
            self.cache.sadd(DIRTY_SET_KEY, str(item_id))
            pending = self.pending_dirty_writes()
        self.metrics.write_back_queue(pending)
        return item

    def flush(self, batch_size: int | None = None) -> int:
        with self._flush_lock:
            dirty_ids = sorted(self.cache.smembers(DIRTY_SET_KEY), key=lambda value: int(value))
            if batch_size is not None:
                dirty_ids = dirty_ids[:batch_size]

            flushed_ids: list[str] = []
            for raw_item_id in dirty_ids:
                cached = self.cache.get(_item_key(int(raw_item_id)))
                if cached is None:
                    flushed_ids.append(raw_item_id)
                    continue
                item = _decode_item(cached)
                self.db.upsert_item(
                    int(item["id"]),
                    str(item["value"]),
                    name=str(item["name"]),
                    updated_at=float(item["updated_at"]),
                )
                flushed_ids.append(raw_item_id)

            if flushed_ids:
                self.cache.srem(DIRTY_SET_KEY, *flushed_ids)

        if flushed_ids:
            self.metrics.db_write(len(flushed_ids))
            self.metrics.write_back_flush(len(flushed_ids))

        return len(flushed_ids)

    def pending_dirty_writes(self) -> int:
        return self.cache.scard(DIRTY_SET_KEY)

    async def flush_forever(self, interval_seconds: float, batch_size: int) -> None:
        while True:
            await asyncio.sleep(interval_seconds)
            self.flush(batch_size=batch_size)


def build_strategy(
    name: str,
    cache: RedisCache,
    db: Database,
    metrics: Metrics,
) -> CacheStrategy:
    if name == "cache_aside":
        return CacheAsideStrategy(cache, db, metrics)
    if name == "write_through":
        return WriteThroughStrategy(cache, db, metrics)
    if name == "write_back":
        return WriteBackStrategy(cache, db, metrics)
    raise ValueError(f"Unknown cache strategy: {name}")


def _item_key(item_id: int) -> str:
    return f"item:{item_id}"


def _encode_item(item: dict) -> str:
    return json.dumps(item, ensure_ascii=False, separators=(",", ":"))


def _decode_item(raw: str) -> dict:
    return json.loads(raw)
