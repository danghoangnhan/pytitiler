"""Tests for the TiTiler-PgSTAC API client (mocked HTTP)."""

from __future__ import annotations


import httpx
import pytest

from pytitiler import TiTilerPgSTAC
from pytitiler.models import (
    ImageType,
    MosaicPointResponse,
    PgSTACParams,
    RegisterResponse,
    SearchInfo,
    SearchList,
    TileJSON,
    TileParams,
)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _json_response(data: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=data,
        headers={"content-type": "application/json"},
    )


def _bytes_response(content: bytes, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        content=content,
        headers={"content-type": "image/tiff"},
    )


def _make_client(handler) -> TiTilerPgSTAC:
    """Create a TiTilerPgSTAC with a mocked transport."""
    transport = httpx.MockTransport(handler)
    client = TiTilerPgSTAC("http://test", timeout=5.0)
    mock_http = httpx.AsyncClient(base_url="http://test", transport=transport)
    client._async_client._http = mock_http
    for attr in ("searches", "collections", "items", "algorithms", "colormaps", "tiling_schemes"):
        getattr(client._async_client, attr)._http = mock_http
    return client


def _route_handler(routes: dict):
    """Build a handler from a dict of 'METHOD /path' -> Response."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.raw_path.decode().split("?")[0]
        key = f"{request.method} {path}"
        if key in routes:
            return routes[key]
        # Partial match for parameterized routes
        for route_key, response in routes.items():
            method, route_path = route_key.split(" ", 1)
            if request.method == method and path.startswith(route_path):
                return response
        return httpx.Response(404, json={"detail": f"Not found: {key}"})
    return handler


# ──────────────────────────────────────────────
# Search API tests
# ──────────────────────────────────────────────

@pytest.mark.unit
class TestSearchAPI:
    def test_register(self):
        client = _make_client(_route_handler({
            "POST /searches/register": _json_response({"id": "abc123"}),
        }))
        with client:
            result = client.searches.register(collections=["sentinel-2"])
            assert isinstance(result, RegisterResponse)
            assert result.id == "abc123"

    def test_list(self):
        client = _make_client(_route_handler({
            "GET /searches/list": _json_response({
                "searches": [{
                    "search": {
                        "hash": "h1",
                        "search": {},
                        "lastused": "2026-01-01T00:00:00Z",
                        "usecount": 5,
                        "metadata": {"type": "mosaic"},
                    },
                    "links": [],
                }],
                "context": {"returned": 1},
            }),
        }))
        with client:
            result = client.searches.list(limit=10)
            assert isinstance(result, SearchList)
            assert result.context.returned == 1
            assert len(result.searches) == 1

    def test_tile(self):
        tile_bytes = b"\x00\x01\x02\x03"
        client = _make_client(_route_handler({
            "GET /searches/abc/tiles/WebMercatorQuad/10/512/384.tif": _bytes_response(tile_bytes),
        }))
        with client:
            result = client.searches.tile("abc", "WebMercatorQuad", 10, 512, 384)
            assert result == tile_bytes

    def test_tilejson(self):
        tj_data = {
            "tilejson": "3.0.0",
            "tiles": ["http://test/searches/abc/tiles/WebMercatorQuad/{z}/{x}/{y}.png"],
            "minzoom": 0,
            "maxzoom": 18,
        }
        client = _make_client(_route_handler({
            "GET /searches/abc/WebMercatorQuad/tilejson.json": _json_response(tj_data),
        }))
        with client:
            result = client.searches.tilejson("abc", "WebMercatorQuad")
            assert isinstance(result, TileJSON)
            assert len(result.tiles) == 1
            assert result.maxzoom == 18

    def test_point(self):
        client = _make_client(_route_handler({
            "GET /searches/abc/point/12.5,45.3": _json_response({
                "coordinates": [12.5, 45.3],
                "assets": [{"name": "visual", "values": [100, 200, 150], "band_names": ["b1", "b2", "b3"]}],
            }),
        }))
        with client:
            result = client.searches.point("abc", 12.5, 45.3)
            assert isinstance(result, MosaicPointResponse)
            assert len(result.assets) == 1

    def test_info(self):
        client = _make_client(_route_handler({
            "GET /searches/abc/info": _json_response({
                "search": {
                    "hash": "abc",
                    "search": {},
                    "lastused": "2026-01-01T00:00:00Z",
                    "usecount": 1,
                    "metadata": {"type": "mosaic"},
                },
            }),
        }))
        with client:
            result = client.searches.info("abc")
            assert isinstance(result, SearchInfo)
            assert result.search.hash == "abc"


# ──────────────────────────────────────────────
# Parameter merging tests
# ──────────────────────────────────────────────

@pytest.mark.unit
class TestParamMerging:
    def test_tile_params_passed_as_query(self):
        captured_params: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_params.update(dict(request.url.params))
            return _bytes_response(b"tile-data")

        client = _make_client(handler)
        with client:
            client.searches.tile(
                "abc", "WebMercatorQuad", 10, 512, 384,
                tile_params=TileParams(assets=["visual"], resampling="bilinear"),
                pgstac_params=PgSTACParams(items_limit=50),
            )

        assert "items_limit" in captured_params
        assert captured_params["items_limit"] == "50"

    def test_none_params_excluded(self):
        captured_params: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_params.update(dict(request.url.params))
            return _bytes_response(b"tile-data")

        client = _make_client(handler)
        with client:
            client.searches.tile(
                "abc", "WebMercatorQuad", 10, 512, 384,
                tile_params=TileParams(assets=["visual"]),
            )

        assert "resampling" not in captured_params
        assert "nodata" not in captured_params


# ──────────────────────────────────────────────
# Sync wrapper tests
# ──────────────────────────────────────────────

@pytest.mark.unit
class TestSyncClient:
    def test_health(self):
        client = _make_client(_route_handler({
            "GET /healthz": httpx.Response(200, text="ok"),
        }))
        with client:
            result = client.health()
            assert result == "ok"

    def test_search_register_sync(self):
        client = _make_client(_route_handler({
            "POST /searches/register": _json_response({"id": "sync123"}),
        }))
        with client:
            result = client.searches.register(collections=["test"])
            assert result.id == "sync123"


# ──────────────────────────────────────────────
# URL construction tests
# ──────────────────────────────────────────────

@pytest.mark.unit
class TestURLConstruction:
    def test_collection_tile_url(self):
        captured_path = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_path["path"] = request.url.raw_path.decode()
            return _bytes_response(b"tile")

        client = _make_client(handler)
        with client:
            client.collections.tile("sentinel-2", "WebMercatorQuad", 10, 512, 384)

        assert captured_path["path"] == "/collections/sentinel-2/tiles/WebMercatorQuad/10/512/384.tif"

    def test_item_preview_url(self):
        captured_path = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_path["path"] = request.url.raw_path.decode()
            return _bytes_response(b"preview")

        client = _make_client(handler)
        with client:
            client.items.preview(
                "sentinel-2", "S2A_123",
                width=512, height=512, format=ImageType.png,
            )

        assert captured_path["path"] == "/collections/sentinel-2/items/S2A_123/preview/512x512.png"

    def test_search_bbox_url(self):
        captured_path = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_path["path"] = request.url.raw_path.decode()
            return _bytes_response(b"bbox-image")

        client = _make_client(handler)
        with client:
            client.searches.bbox_image(
                "abc", (10.0, 45.0, 11.0, 46.0),
                width=256, height=256, format=ImageType.png,
            )

        assert captured_path["path"] == "/searches/abc/bbox/10.0,45.0,11.0,46.0/256x256.png"

    def test_item_info_url(self):
        captured_path = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_path["path"] = request.url.raw_path.decode()
            return _json_response({
                "bounds": [0, 0, 1, 1],
                "crs": "EPSG:4326",
                "band_metadata": [["b1", {}]],
                "band_descriptions": [["b1", "Band 1"]],
                "dtype": "uint8",
                "nodata_type": "None",
            })

        client = _make_client(handler)
        with client:
            client.items.info("sentinel-2", "S2A_123")

        assert captured_path["path"] == "/collections/sentinel-2/items/S2A_123/info"

    def test_search_wmts_url(self):
        captured_path = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_path["path"] = request.url.raw_path.decode()
            return httpx.Response(200, text="<xml/>", headers={"content-type": "application/xml"})

        client = _make_client(handler)
        with client:
            result = client.searches.wmts("abc")

        assert captured_path["path"] == "/searches/abc/WMTSCapabilities.xml"
        assert result == "<xml/>"


# ──────────────────────────────────────────────
# Error-path tests
# ──────────────────────────────────────────────

@pytest.mark.unit
class TestErrorPaths:
    def test_http_404_raises_status_error(self):
        client = _make_client(_route_handler({
            "GET /searches/missing/info": httpx.Response(404, json={"detail": "Not found"}),
        }))
        with client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                client.searches.info("missing")
            assert exc_info.value.response.status_code == 404

    def test_http_500_raises_status_error(self):
        client = _make_client(lambda req: httpx.Response(500, json={"detail": "Internal error"}))
        with client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                client.searches.register(collections=["fail"])
            assert exc_info.value.response.status_code == 500

    def test_merge_params_all_none_returns_empty_dict(self):
        """_merge_params with no models returns an empty dict, not None."""
        from pytitiler._base import BaseAPI
        result = BaseAPI._merge_params(None, None)
        assert result == {}
        assert isinstance(result, dict)

    def test_merge_params_no_args_returns_empty_dict(self):
        from pytitiler._base import BaseAPI
        result = BaseAPI._merge_params()
        assert result == {}

    def test_sync_proxy_dir_includes_async_methods(self):
        """_SyncProxy.__dir__ exposes async API methods for discoverability."""
        client = _make_client(lambda req: httpx.Response(200, json={}))
        with client:
            methods = dir(client.searches)
            assert "register" in methods
            assert "tile" in methods
            assert "tilejson" in methods
            assert "point" in methods
