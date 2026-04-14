"""AsyncCollectionAPI — /collections/* endpoints."""

from __future__ import annotations

from pytitiler._base import RasterEndpointsMixin
from pytitiler.models import (
    BboxParams,
    DatasetInfo,
    ImageType,
    MosaicPointResponse,
    PgSTACParams,
    TileJSON,
    TileParams,
)


class AsyncCollectionAPI(RasterEndpointsMixin):
    """Stateless API for /collections/{collection_id}/* endpoints."""

    @staticmethod
    def _prefix(collection_id: str) -> str:
        return f"/collections/{collection_id}"

    # ── Delegated raster operations ───────────────

    async def tile(
        self,
        collection_id: str,
        tms: str,
        z: int,
        x: int,
        y: int,
        *,
        format: str | ImageType = ImageType.tif,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        return await self._tile(
            self._prefix(collection_id),
            tms,
            z,
            x,
            y,
            format=format,
            tile_params=tile_params,
            pgstac_params=pgstac_params,
        )

    async def tilejson(
        self,
        collection_id: str,
        tms: str,
        *,
        tile_format: ImageType | None = None,
        tile_scale: int | None = None,
        minzoom: int | None = None,
        maxzoom: int | None = None,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> TileJSON:
        return await self._tilejson(
            self._prefix(collection_id),
            tms,
            tile_format=tile_format,
            tile_scale=tile_scale,
            minzoom=minzoom,
            maxzoom=maxzoom,
            tile_params=tile_params,
            pgstac_params=pgstac_params,
        )

    async def point(
        self,
        collection_id: str,
        lon: float,
        lat: float,
        *,
        coord_crs: str | None = None,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> MosaicPointResponse:
        result = await self._point(
            self._prefix(collection_id),
            lon,
            lat,
            coord_crs=coord_crs,
            tile_params=tile_params,
            pgstac_params=pgstac_params,
        )
        if not isinstance(result, MosaicPointResponse):
            msg = f"Expected MosaicPointResponse, got {type(result).__name__}"
            raise TypeError(msg)
        return result

    async def bbox_image(
        self,
        collection_id: str,
        bbox: tuple[float, float, float, float],
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType = ImageType.tif,
        bbox_params: BboxParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        return await self._bbox_image(
            self._prefix(collection_id),
            bbox,
            width=width,
            height=height,
            format=format,
            bbox_params=bbox_params,
            pgstac_params=pgstac_params,
        )

    async def feature_image(
        self,
        collection_id: str,
        feature: dict,
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType = ImageType.tif,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        return await self._feature_image(
            self._prefix(collection_id),
            feature,
            width=width,
            height=height,
            format=format,
            tile_params=tile_params,
            pgstac_params=pgstac_params,
        )

    async def statistics(
        self,
        collection_id: str,
        feature: dict,
        *,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> dict:
        return await self._statistics(
            self._prefix(collection_id),
            feature,
            tile_params=tile_params,
            pgstac_params=pgstac_params,
        )

    async def info(self, collection_id: str) -> DatasetInfo:
        result = await self._info(self._prefix(collection_id))
        if not isinstance(result, DatasetInfo):
            raise TypeError(f"Expected DatasetInfo, got {type(result).__name__}")
        return result

    async def wmts(self, collection_id: str) -> str:
        return await self._wmts(self._prefix(collection_id))

    async def assets_for_tile(
        self,
        collection_id: str,
        tms: str,
        z: int,
        x: int,
        y: int,
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        return await self._assets_for_tile(
            self._prefix(collection_id),
            tms,
            z,
            x,
            y,
            pgstac_params=pgstac_params,
        )

    async def assets_for_bbox(
        self,
        collection_id: str,
        bbox: tuple[float, float, float, float],
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        return await self._assets_for_bbox(
            self._prefix(collection_id),
            bbox,
            pgstac_params=pgstac_params,
        )

    async def assets_for_point(
        self,
        collection_id: str,
        lon: float,
        lat: float,
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        return await self._assets_for_point(
            self._prefix(collection_id),
            lon,
            lat,
            pgstac_params=pgstac_params,
        )

    def map_viewer_url(self, collection_id: str, tms: str) -> str:
        return self._map_viewer_url(self._prefix(collection_id), tms)
