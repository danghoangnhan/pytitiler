"""AsyncItemAPI — /collections/{collection_id}/items/{item_id}/* endpoints."""

from __future__ import annotations

from pytitiler._base import RasterEndpointsMixin
from pytitiler.models import (
    BandStatistics,
    BboxParams,
    DatasetInfo,
    ImageType,
    InfoGeoJSON,
    PointResponse,
    RenderItemList,
    RenderItemWithLinks,
    TileJSON,
    TileParams,
    TileSet,
    TileSetList,
)


class AsyncItemAPI(RasterEndpointsMixin):
    """Stateless API for /collections/{collection_id}/items/{item_id}/* endpoints."""

    @staticmethod
    def _prefix(collection_id: str, item_id: str) -> str:
        return f"/collections/{collection_id}/items/{item_id}"

    # ── Delegated raster operations ───────────────

    async def tile(
        self,
        collection_id: str,
        item_id: str,
        tms: str,
        z: int,
        x: int,
        y: int,
        *,
        scale: int | None = None,
        format: str | ImageType | None = ImageType.tif,
        tile_params: TileParams | None = None,
    ) -> bytes:
        return await self._tile(
            self._prefix(collection_id, item_id),
            tms,
            z,
            x,
            y,
            scale=scale,
            format=format,
            tile_params=tile_params,
        )

    async def tilejson(
        self,
        collection_id: str,
        item_id: str,
        tms: str,
        *,
        tile_format: ImageType | None = None,
        tile_scale: int | None = None,
        minzoom: int | None = None,
        maxzoom: int | None = None,
        tile_params: TileParams | None = None,
    ) -> TileJSON:
        return await self._tilejson(
            self._prefix(collection_id, item_id),
            tms,
            tile_format=tile_format,
            tile_scale=tile_scale,
            minzoom=minzoom,
            maxzoom=maxzoom,
            tile_params=tile_params,
        )

    async def point(
        self,
        collection_id: str,
        item_id: str,
        lon: float,
        lat: float,
        *,
        coord_crs: str | None = None,
        tile_params: TileParams | None = None,
    ) -> PointResponse:
        result = await self._point(
            self._prefix(collection_id, item_id),
            lon,
            lat,
            coord_crs=coord_crs,
            tile_params=tile_params,
        )
        if not isinstance(result, PointResponse):
            raise TypeError(f"Expected PointResponse, got {type(result).__name__}")
        return result

    async def bbox_image(
        self,
        collection_id: str,
        item_id: str,
        bbox: tuple[float, float, float, float],
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType = ImageType.tif,
        bbox_params: BboxParams | None = None,
    ) -> bytes:
        return await self._bbox_image(
            self._prefix(collection_id, item_id),
            bbox,
            width=width,
            height=height,
            format=format,
            bbox_params=bbox_params,
        )

    async def feature_image(
        self,
        collection_id: str,
        item_id: str,
        feature: dict,
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType | None = ImageType.tif,
        tile_params: TileParams | None = None,
    ) -> bytes:
        return await self._feature_image(
            self._prefix(collection_id, item_id),
            feature,
            width=width,
            height=height,
            format=format,
            tile_params=tile_params,
        )

    async def statistics(
        self,
        collection_id: str,
        item_id: str,
        feature: dict | None = None,
        *,
        tile_params: TileParams | None = None,
    ) -> dict[str, BandStatistics]:
        prefix = self._prefix(collection_id, item_id)
        params = self._merge_params(tile_params)
        if feature is not None:
            resp = await self._post(f"{prefix}/statistics", json=feature, params=params)
        else:
            resp = await self._get(f"{prefix}/statistics", params=params)
        data = resp.json()
        return {k: BandStatistics.model_validate(v) for k, v in data.items()}

    async def info(self, collection_id: str, item_id: str) -> DatasetInfo:
        result = await self._info(self._prefix(collection_id, item_id))
        if not isinstance(result, DatasetInfo):
            raise TypeError(f"Expected DatasetInfo, got {type(result).__name__}")
        return result

    async def info_geojson(self, collection_id: str, item_id: str) -> InfoGeoJSON:
        prefix = self._prefix(collection_id, item_id)
        resp = await self._get(f"{prefix}/info.geojson")
        return InfoGeoJSON.model_validate(resp.json())

    async def wmts(self, collection_id: str, item_id: str) -> str:
        return await self._wmts(self._prefix(collection_id, item_id))

    # ── Item-specific endpoints ───────────────────

    async def preview(
        self,
        collection_id: str,
        item_id: str,
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType | None = None,
        tile_params: TileParams | None = None,
    ) -> bytes:
        prefix = self._prefix(collection_id, item_id)
        params = self._merge_params(tile_params)

        if width is not None and height is not None and format is not None:
            path = f"{prefix}/preview/{width}x{height}.{format}"
        elif format is not None:
            path = f"{prefix}/preview.{format}"
        else:
            path = f"{prefix}/preview"

        resp = await self._get(path, params=params, accept="image/*")
        return resp.content

    async def assets(self, collection_id: str, item_id: str) -> list[str]:
        prefix = self._prefix(collection_id, item_id)
        resp = await self._get(f"{prefix}/assets")
        return resp.json()

    async def asset_statistics(
        self, collection_id: str, item_id: str
    ) -> dict[str, dict[str, BandStatistics]]:
        prefix = self._prefix(collection_id, item_id)
        resp = await self._get(f"{prefix}/asset_statistics")
        data = resp.json()
        return {
            asset: {band: BandStatistics.model_validate(v) for band, v in bands.items()}
            for asset, bands in data.items()
        }

    async def renders(self, collection_id: str, item_id: str) -> RenderItemList:
        prefix = self._prefix(collection_id, item_id)
        resp = await self._get(f"{prefix}/renders")
        return RenderItemList.model_validate(resp.json())

    async def render(
        self, collection_id: str, item_id: str, render_id: str
    ) -> RenderItemWithLinks:
        prefix = self._prefix(collection_id, item_id)
        resp = await self._get(f"{prefix}/renders/{render_id}")
        return RenderItemWithLinks.model_validate(resp.json())

    async def available_tiles(self, collection_id: str, item_id: str) -> TileSetList:
        return await self._available_tiles(self._prefix(collection_id, item_id))

    async def tile_matrix_info(
        self, collection_id: str, item_id: str, tms: str
    ) -> TileSet:
        return await self._tile_matrix_info(self._prefix(collection_id, item_id), tms)

    def map_viewer_url(self, collection_id: str, item_id: str, tms: str) -> str:
        return self._map_viewer_url(self._prefix(collection_id, item_id), tms)
