"""Base API class and RasterEndpointsMixin for shared HTTP + raster operations."""

from __future__ import annotations

import httpx
from pydantic import BaseModel

from pytitiler.models import (
    BboxParams,
    DatasetInfo,
    ImageType,
    MosaicPointResponse,
    PgSTACParams,
    PointResponse,
    SearchInfo,
    TileJSON,
    TileParams,
)


class BaseAPI:
    """Shared HTTP plumbing for all sub-resource APIs."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def _get(
        self,
        path: str,
        *,
        params: dict | None = None,
        accept: str = "application/json",
    ) -> httpx.Response:
        response = await self._http.get(
            path,
            params=params,
            headers={"Accept": accept},
        )
        response.raise_for_status()
        return response

    async def _post(
        self,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        response = await self._http.post(path, json=json, params=params)
        response.raise_for_status()
        return response

    @staticmethod
    def _merge_params(*param_models: BaseModel | None) -> dict:
        """Merge Pydantic param models into a flat query dict, dropping None values."""
        merged: dict = {}
        for model in param_models:
            if model is None:
                continue
            for key, value in model.model_dump(exclude_none=True).items():
                merged[key] = value
        return merged


class RasterEndpointsMixin(BaseAPI):
    """Shared raster operations across searches, collections, and items."""

    async def _tile(
        self,
        prefix: str,
        tms: str,
        z: int,
        x: int,
        y: int,
        *,
        format: str | ImageType = ImageType.tif,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        fmt = format.value if isinstance(format, ImageType) else format
        path = f"{prefix}/tiles/{tms}/{z}/{x}/{y}.{fmt}"
        params = self._merge_params(tile_params, pgstac_params)
        resp = await self._get(path, params=params, accept="image/*")
        return resp.content

    async def _tilejson(
        self,
        prefix: str,
        tms: str,
        *,
        tile_format: ImageType | None = None,
        tile_scale: int | None = None,
        minzoom: int | None = None,
        maxzoom: int | None = None,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> TileJSON:
        path = f"{prefix}/{tms}/tilejson.json"
        params = self._merge_params(tile_params, pgstac_params)
        if tile_format is not None:
            params["tile_format"] = tile_format.value
        if tile_scale is not None:
            params["tile_scale"] = tile_scale
        if minzoom is not None:
            params["minzoom"] = minzoom
        if maxzoom is not None:
            params["maxzoom"] = maxzoom
        resp = await self._get(path, params=params)
        return TileJSON.model_validate(resp.json())

    async def _point(
        self,
        prefix: str,
        lon: float,
        lat: float,
        *,
        coord_crs: str | None = None,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> MosaicPointResponse | PointResponse:
        path = f"{prefix}/point/{lon},{lat}"
        params = self._merge_params(tile_params, pgstac_params)
        if coord_crs is not None:
            params["coord_crs"] = coord_crs
        resp = await self._get(path, params=params)
        data = resp.json()
        if "assets" in data:
            return MosaicPointResponse.model_validate(data)
        return PointResponse.model_validate(data)

    async def _bbox_image(
        self,
        prefix: str,
        bbox: tuple[float, float, float, float],
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType = ImageType.tif,
        bbox_params: BboxParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        fmt = format.value if isinstance(format, ImageType) else format
        minx, miny, maxx, maxy = bbox
        if width is not None and height is not None:
            path = f"{prefix}/bbox/{minx},{miny},{maxx},{maxy}/{width}x{height}.{fmt}"
        else:
            path = f"{prefix}/bbox/{minx},{miny},{maxx},{maxy}.{fmt}"
        params = self._merge_params(bbox_params, pgstac_params)
        resp = await self._get(path, params=params, accept="image/*")
        return resp.content

    async def _feature_image(
        self,
        prefix: str,
        feature: dict,
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType = ImageType.tif,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        fmt = format.value if isinstance(format, ImageType) else format
        if width is not None and height is not None:
            path = f"{prefix}/feature/{width}x{height}.{fmt}"
        else:
            path = f"{prefix}/feature.{fmt}"
        params = self._merge_params(tile_params, pgstac_params)
        resp = await self._post(path, json=feature, params=params)
        return resp.content

    async def _statistics(
        self,
        prefix: str,
        feature: dict,
        *,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> dict:
        path = f"{prefix}/statistics"
        params = self._merge_params(tile_params, pgstac_params)
        resp = await self._post(path, json=feature, params=params)
        return resp.json()

    async def _info(self, prefix: str) -> DatasetInfo | SearchInfo:
        resp = await self._get(f"{prefix}/info")
        data = resp.json()
        if "search" in data:
            return SearchInfo.model_validate(data)
        return DatasetInfo.model_validate(data)

    async def _wmts(self, prefix: str) -> str:
        resp = await self._get(
            f"{prefix}/WMTSCapabilities.xml",
            accept="application/xml",
        )
        return resp.text

    async def _assets_for_tile(
        self,
        prefix: str,
        tms: str,
        z: int,
        x: int,
        y: int,
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        path = f"{prefix}/tiles/{tms}/{z}/{x}/{y}/assets"
        params = self._merge_params(pgstac_params)
        resp = await self._get(path, params=params)
        return resp.json()

    async def _assets_for_bbox(
        self,
        prefix: str,
        bbox: tuple[float, float, float, float],
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        minx, miny, maxx, maxy = bbox
        path = f"{prefix}/bbox/{minx},{miny},{maxx},{maxy}/assets"
        params = self._merge_params(pgstac_params)
        resp = await self._get(path, params=params)
        return resp.json()

    async def _assets_for_point(
        self,
        prefix: str,
        lon: float,
        lat: float,
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        path = f"{prefix}/point/{lon},{lat}/assets"
        params = self._merge_params(pgstac_params)
        resp = await self._get(path, params=params)
        return resp.json()

    def _map_viewer_url(self, prefix: str, tms: str) -> str:
        return f"{self._http.base_url}{prefix}/{tms}/map.html"
