from __future__ import annotations

from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        with getattr(self, "_lock", Lock()):
            self.cache_hits = 0
            self.cache_misses = 0
            self.db_reads = 0
            self.db_writes = 0
            self.read_requests = 0
            self.write_requests = 0
            self.write_back_queued = 0
            self.write_back_flushed = 0
            self.write_back_pending_max = 0

    def read_request(self) -> None:
        with self._lock:
            self.read_requests += 1

    def write_request(self) -> None:
        with self._lock:
            self.write_requests += 1

    def cache_hit(self) -> None:
        with self._lock:
            self.cache_hits += 1

    def cache_miss(self) -> None:
        with self._lock:
            self.cache_misses += 1

    def db_read(self) -> None:
        with self._lock:
            self.db_reads += 1

    def db_write(self, count: int = 1) -> None:
        with self._lock:
            self.db_writes += count

    def write_back_queue(self, pending: int) -> None:
        with self._lock:
            self.write_back_queued += 1
            if pending > self.write_back_pending_max:
                self.write_back_pending_max = pending

    def write_back_flush(self, count: int) -> None:
        with self._lock:
            self.write_back_flushed += count

    def snapshot(self, pending_dirty_writes: int = 0) -> dict:
        with self._lock:
            cache_total = self.cache_hits + self.cache_misses
            hit_rate = self.cache_hits / cache_total if cache_total else 0.0
            return {
                "requests": {
                    "read": self.read_requests,
                    "write": self.write_requests,
                    "total": self.read_requests + self.write_requests,
                },
                "cache": {
                    "hits": self.cache_hits,
                    "misses": self.cache_misses,
                    "hit_rate": round(hit_rate, 4),
                },
                "db": {
                    "reads": self.db_reads,
                    "writes": self.db_writes,
                    "accesses": self.db_reads + self.db_writes,
                },
                "write_back": {
                    "queued": self.write_back_queued,
                    "flushed": self.write_back_flushed,
                    "pending": pending_dirty_writes,
                    "pending_max": self.write_back_pending_max,
                },
            }

