from __future__ import annotations

from typing import Iterable
import socket


class CacheError(RuntimeError):
    pass


class RedisCache:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "",
        timeout: float = 3.0,
    ) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.prefix = prefix.strip(":")
        self.timeout = timeout

    def get(self, key: str) -> str | None:
        return self._execute("GET", self._key(key))

    def set(self, key: str, value: str) -> None:
        self._execute("SET", self._key(key), value)

    def delete(self, key: str) -> None:
        self._execute("DEL", self._key(key))

    def clear(self) -> None:
        self._execute("FLUSHDB")

    def sadd(self, key: str, member: str) -> None:
        self._execute("SADD", self._key(key), member)

    def srem(self, key: str, *members: str) -> None:
        if members:
            self._execute("SREM", self._key(key), *members)

    def smembers(self, key: str) -> set[str]:
        result = self._execute("SMEMBERS", self._key(key))
        return set(result or [])

    def scard(self, key: str) -> int:
        return int(self._execute("SCARD", self._key(key)))

    def ping(self) -> bool:
        return self._execute("PING") == "PONG"

    def _key(self, key: str) -> str:
        if not self.prefix:
            return key
        return f"{self.prefix}:{key}"

    def _execute(self, *args: object):
        try:
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                reader = sock.makefile("rb")
                if self.db:
                    sock.sendall(_encode_command(("SELECT", self.db)))
                    _raise_on_error(_read_response(reader))
                sock.sendall(_encode_command(args))
                return _raise_on_error(_read_response(reader))
        except OSError as exc:
            raise CacheError(f"Redis is unavailable at {self.host}:{self.port}: {exc}") from exc


def _encode_command(args: Iterable[object]) -> bytes:
    parts = list(args)
    encoded = [f"*{len(parts)}\r\n".encode("ascii")]
    for arg in parts:
        data = str(arg).encode("utf-8")
        encoded.append(f"${len(data)}\r\n".encode("ascii"))
        encoded.append(data + b"\r\n")
    return b"".join(encoded)


def _read_response(reader):
    marker = reader.read(1)
    if not marker:
        raise CacheError("Redis closed the connection")
    line = reader.readline()

    if marker == b"+":
        return line[:-2].decode("utf-8")
    if marker == b"-":
        return CacheError(line[:-2].decode("utf-8"))
    if marker == b":":
        return int(line[:-2])
    if marker == b"$":
        length = int(line[:-2])
        if length == -1:
            return None
        data = reader.read(length)
        reader.read(2)
        return data.decode("utf-8")
    if marker == b"*":
        count = int(line[:-2])
        if count == -1:
            return None
        return [_raise_on_error(_read_response(reader)) for _ in range(count)]

    raise CacheError(f"Unsupported Redis response marker: {marker!r}")


def _raise_on_error(value):
    if isinstance(value, CacheError):
        raise value
    return value
