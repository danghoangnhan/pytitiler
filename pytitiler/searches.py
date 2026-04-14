"""AsyncSearchAPI — /searches/* endpoints."""

from __future__ import annotations

from pytitiler._base import RasterEndpointsMixin
from pytitiler.models import (
    BboxParams,
    ImageType,
    MosaicMetadata,
    MosaicPointResponse,
    PgSTACParams,
    RegisterMosaicRequest,
    RegisterResponse,
    SearchInfo,
    SearchList,
    SortExtension,
    TileJSON,
    TileParams,
)


class AsyncSearchAPI(RasterEndpointsMixin):
    """Stateless API for /searches/* endpoints."""

    @staticmethod
    def _prefix(search_id: str) -> str:
        return f"/searches/{search_id}"

    # ── Search-specific endpoints ─────────────────

    async def register(
        self,
        *,
        collections: list[str] | None = None,
        ids: list[str] | None = None,
        bbox: tuple[float, ...] | None = None,
        intersects: dict | None = None,
        datetime: str | None = None,
        query: dict | None = None,
        sortby: list[SortExtension] | None = None,
        filter: dict | None = None,
        metadata: MosaicMetadata | None = None,
    ) -> RegisterResponse:
        body = RegisterMosaicRequest(
            collections=collections,
            ids=ids,
            bbox=bbox,
            intersects=intersects,
            datetime=datetime,
            query=query,
            sortby=sortby,
            filter=filter,
            metadata=metadata,
        )
        resp = await self._post(
            "/searches/register",
            json=body.model_dump(exclude_none=True, by_alias=True),
        )
        return RegisterResponse.model_validate(resp.json())

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sortby: str | None = None,
    ) -> SearchList:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sortby is not None:
            params["sortby"] = sortby
        resp = await self._get("/searches/list", params=params or None)
        return SearchList.model_validate(resp.json())

    # ── Delegated raster operations ───────────────

    async def tile(
        self,
        search_id: str,
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
            self._prefix(search_id),
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
        search_id: str,
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
            self._prefix(search_id),
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
        search_id: str,
        lon: float,
        lat: float,
        *,
        coord_crs: str | None = None,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> MosaicPointResponse:
        result = await self._point(
            self._prefix(search_id),
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
        search_id: str,
        bbox: tuple[float, float, float, float],
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType = ImageType.tif,
        bbox_params: BboxParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        return await self._bbox_image(
            self._prefix(search_id),
            bbox,
            width=width,
            height=height,
            format=format,
            bbox_params=bbox_params,
            pgstac_params=pgstac_params,
        )

    async def feature_image(
        self,
        search_id: str,
        feature: dict,
        *,
        width: int | None = None,
        height: int | None = None,
        format: str | ImageType = ImageType.tif,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> bytes:
        return await self._feature_image(
            self._prefix(search_id),
            feature,
            width=width,
            height=height,
            format=format,
            tile_params=tile_params,
            pgstac_params=pgstac_params,
        )

    async def statistics(
        self,
        search_id: str,
        feature: dict,
        *,
        tile_params: TileParams | None = None,
        pgstac_params: PgSTACParams | None = None,
    ) -> dict:
        return await self._statistics(
            self._prefix(search_id),
            feature,
            tile_params=tile_params,
            pgstac_params=pgstac_params,
        )

    async def info(self, search_id: str) -> SearchInfo:
        result = await self._info(self._prefix(search_id))
        if not isinstance(result, SearchInfo):
            raise TypeError(f"Expected SearchInfo, got {type(result).__name__}")
        return result

    async def wmts(self, search_id: str) -> str:
        return await self._wmts(self._prefix(search_id))

    async def assets_for_tile(
        self,
        search_id: str,
        tms: str,
        z: int,
        x: int,
        y: int,
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        return await self._assets_for_tile(
            self._prefix(search_id),
            tms,
            z,
            x,
            y,
            pgstac_params=pgstac_params,
        )

    async def assets_for_bbox(
        self,
        search_id: str,
        bbox: tuple[float, float, float, float],
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        return await self._assets_for_bbox(
            self._prefix(search_id),
            bbox,
            pgstac_params=pgstac_params,
        )

    async def assets_for_point(
        self,
        search_id: str,
        lon: float,
        lat: float,
        *,
        pgstac_params: PgSTACParams | None = None,
    ) -> list[dict]:
        return await self._assets_for_point(
            self._prefix(search_id),
            lon,
            lat,
            pgstac_params=pgstac_params,
        )

    def map_viewer_url(self, search_id: str, tms: str) -> str:
        return self._map_viewer_url(self._prefix(search_id), tms)
