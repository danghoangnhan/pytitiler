"""Client entry points: AsyncTiTilerPgSTAC (async) and TiTilerPgSTAC (sync wrapper)."""

from __future__ import annotations

import asyncio
import functools
from typing import Any

import httpx

from pytitiler.collections import AsyncCollectionAPI
from pytitiler.items import AsyncItemAPI
from pytitiler.metadata import (
    AsyncAlgorithmAPI,
    AsyncColorMapAPI,
    AsyncTilingSchemeAPI,
)
from pytitiler.searches import AsyncSearchAPI

# ──────────────────────────────────────────────
# Async client (primary)
# ──────────────────────────────────────────────


class AsyncTiTilerPgSTAC:
    """Async client for titiler-pgstac.

    Usage::

        async with AsyncTiTilerPgSTAC("http://localhost:8081") as c:
            result = await c.searches.register(collections=["sentinel-2"])
            tile = await c.searches.tile(
                result.id, "WebMercatorQuad", 10, 512, 384,
            )
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers or {},
        )
        self.searches = AsyncSearchAPI(self._http)
        self.collections = AsyncCollectionAPI(self._http)
        self.items = AsyncItemAPI(self._http)
        self.algorithms = AsyncAlgorithmAPI(self._http)
        self.colormaps = AsyncColorMapAPI(self._http)
        self.tiling_schemes = AsyncTilingSchemeAPI(self._http)

    async def health(self) -> str:
        """GET /healthz — returns 'ok' if the service is up."""
        resp = await self._http.get("/healthz")
        resp.raise_for_status()
        return resp.text

    async def landing(self) -> dict:
        """GET / — OGC landing page."""
        resp = await self._http.get("/")
        resp.raise_for_status()
        return resp.json()

    async def conformance(self) -> dict:
        """GET /conformance — OGC conformance classes."""
        resp = await self._http.get("/conformance")
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncTiTilerPgSTAC:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()


# ──────────────────────────────────────────────
# Sync wrapper helpers
# ──────────────────────────────────────────────


class _SyncProxy:
    """Wraps an async sub-resource API, running each call in the given event loop."""

    def __init__(self, async_api: Any, loop: asyncio.AbstractEventLoop) -> None:
        self._async = async_api
        self._loop = loop
        self._wrapped: dict[str, Any] = {}
        # Eagerly bind all public methods so they appear as real attributes.
        for name in dir(async_api):
            if name.startswith("_"):
                continue
            attr = getattr(async_api, name)
            if callable(attr):

                @functools.wraps(attr)
                def _make_wrapper(fn: Any = attr) -> Any:
                    def wrapper(*args: Any, **kwargs: Any) -> Any:
                        return loop.run_until_complete(fn(*args, **kwargs))

                    return wrapper

                self._wrapped[name] = _make_wrapper()

    def __getattr__(self, name: str) -> Any:
        if name in self._wrapped:
            return self._wrapped[name]
        return getattr(self._async, name)

    def __dir__(self) -> list[str]:
        return list(set(super().__dir__()) | set(dir(self._async)))


# ──────────────────────────────────────────────
# Sync client
# ──────────────────────────────────────────────


class TiTilerPgSTAC:
    """Synchronous client for titiler-pgstac.

    Wraps :class:`AsyncTiTilerPgSTAC` with a dedicated event loop.

    Usage::

        with TiTilerPgSTAC("http://localhost:8081") as client:
            result = client.searches.register(collections=["sentinel-2"])
            tile = client.searches.tile(result.id, "WebMercatorQuad", 10, 512, 384)
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._loop = asyncio.new_event_loop()
        try:
            self._async_client = AsyncTiTilerPgSTAC(
                base_url,
                timeout=timeout,
                headers=headers,
            )
            self.searches = _SyncProxy(self._async_client.searches, self._loop)
            self.collections = _SyncProxy(self._async_client.collections, self._loop)
            self.items = _SyncProxy(self._async_client.items, self._loop)
            self.algorithms = _SyncProxy(self._async_client.algorithms, self._loop)
            self.colormaps = _SyncProxy(self._async_client.colormaps, self._loop)
            self.tiling_schemes = _SyncProxy(
                self._async_client.tiling_schemes,
                self._loop,
            )
        except Exception:
            self._loop.close()
            raise

    def health(self) -> str:
        return self._loop.run_until_complete(self._async_client.health())

    def landing(self) -> dict:
        return self._loop.run_until_complete(self._async_client.landing())

    def conformance(self) -> dict:
        return self._loop.run_until_complete(self._async_client.conformance())

    def close(self) -> None:
        self._loop.run_until_complete(self._async_client.aclose())
        self._loop.close()

    def __enter__(self) -> TiTilerPgSTAC:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
