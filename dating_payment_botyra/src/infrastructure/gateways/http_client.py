import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class HttpClientError(Exception):
    pass


class HttpClientResponseError(HttpClientError):

    def __init__(self, status: int, body: str, *, method: str, url: str) -> None:
        super().__init__(f"{method} {url} -> HTTP {status}: {body[:200]}")
        self.status = status
        self.body = body


class HttpClient:
    def __init__(
        self,
        *,
        timeout: float = 10.0,
        pool_limit: int = 100,
        pool_limit_per_host: int = 30,
    ) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._connector_kwargs: dict[str, Any] = {
            "limit": pool_limit,
            "limit_per_host": pool_limit_per_host,
            "ttl_dns_cache": 300,
            "enable_cleanup_closed": True,
        }
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        if self._session is not None:
            return
        connector = aiohttp.TCPConnector(**self._connector_kwargs)
        self._session = aiohttp.ClientSession(
            timeout=self._timeout,
            connector=connector,
            raise_for_status=False,
        )
        logger.info("HttpClient started")

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None
            logger.info("HttpClient closed")

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("HttpClient is not started. Call .start() first.")
        return self._session


    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self._request_json("GET", url, params=params, headers=headers)

    async def post_json(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self._request_json("POST", url, json=json, headers=headers)


    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            async with self.session.request(
                method, url, params=params, json=json, headers=headers
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise HttpClientResponseError(
                        resp.status, body, method=method, url=url
                    )
                return await resp.json()
        except aiohttp.ClientError as e:
            raise HttpClientError(f"{method} {url} failed: {e}") from e
