"""Metadata APIs — algorithms, colormaps, tiling schemes."""

from __future__ import annotations

from pytitiler._base import BaseAPI
from pytitiler.models import (
    AlgorithmMetadata,
    AlgorithmRef,
    ColorMapRef,
    TileMatrixSetRef,
)


class AsyncAlgorithmAPI(BaseAPI):
    """GET /algorithms endpoints."""

    async def list(self) -> list[AlgorithmRef]:
        resp = await self._get("/algorithms")
        data = resp.json()
        return [AlgorithmRef.model_validate(a) for a in data.get("algorithms", [])]

    async def get(self, algorithm_id: str) -> AlgorithmMetadata:
        resp = await self._get(f"/algorithms/{algorithm_id}")
        return AlgorithmMetadata.model_validate(resp.json())


class AsyncColorMapAPI(BaseAPI):
    """GET /colorMaps endpoints."""

    async def list(self) -> list[ColorMapRef]:
        resp = await self._get("/colorMaps")
        data = resp.json()
        return [ColorMapRef.model_validate(c) for c in data.get("colormaps", [])]

    async def get(self, colormap_id: str, *, format: str | None = None) -> dict | bytes:
        params = {"format": format} if format else None
        resp = await self._get(f"/colorMaps/{colormap_id}", params=params)
        content_type = resp.headers.get("content-type", "")
        if "image" in content_type:
            return resp.content
        return resp.json()


class AsyncTilingSchemeAPI(BaseAPI):
    """GET /tileMatrixSets endpoints."""

    async def list(self) -> list[TileMatrixSetRef]:
        resp = await self._get("/tileMatrixSets")
        data = resp.json()
        return [
            TileMatrixSetRef.model_validate(t) for t in data.get("tileMatrixSets", [])
        ]

    async def get(self, tms_id: str) -> dict:
        resp = await self._get(f"/tileMatrixSets/{tms_id}")
        return resp.json()
