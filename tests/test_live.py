"""Integration tests for the TiTiler-PgSTAC client against a live instance.

Requires a running titiler-pgstac at http://192.168.3.53:8081.
Run with: uv run pytest tests/integration/test_titiler_client_live.py -v -m integration
"""

from __future__ import annotations

import os

import pytest

from pytitiler import TiTilerPgSTAC
from pytitiler.models import (
    RegisterResponse,
    SearchInfo,
    SearchList,
    TileJSON,
)

TITILER_URL = os.environ.get("TITILER_TEST_URL", "http://192.168.3.53:8081")


@pytest.fixture
def client():
    with TiTilerPgSTAC(TITILER_URL, timeout=30.0) as c:
        yield c


@pytest.mark.integration
class TestHealthAndMetadata:
    def test_health(self, client: TiTilerPgSTAC):
        result = client.health()
        assert "ok" in result.lower() or result.strip() != ""

    def test_landing(self, client: TiTilerPgSTAC):
        result = client.landing()
        assert "links" in result

    def test_conformance(self, client: TiTilerPgSTAC):
        result = client.conformance()
        assert "conformsTo" in result

    def test_list_algorithms(self, client: TiTilerPgSTAC):
        result = client.algorithms.list()
        assert isinstance(result, list)

    def test_list_colormaps(self, client: TiTilerPgSTAC):
        result = client.colormaps.list()
        assert isinstance(result, list)

    def test_list_tiling_schemes(self, client: TiTilerPgSTAC):
        result = client.tiling_schemes.list()
        assert isinstance(result, list)
        assert any(t.id == "WebMercatorQuad" for t in result)


@pytest.mark.integration
class TestSearchWorkflow:
    def test_register_and_list(self, client: TiTilerPgSTAC):
        result = client.searches.register()
        assert isinstance(result, RegisterResponse)
        assert result.id

        searches = client.searches.list(limit=5)
        assert isinstance(searches, SearchList)
        assert searches.context.returned >= 1

    def test_register_and_info(self, client: TiTilerPgSTAC):
        reg = client.searches.register()
        info = client.searches.info(reg.id)
        assert isinstance(info, SearchInfo)
        assert info.search.hash == reg.id

    def test_register_and_tilejson(self, client: TiTilerPgSTAC):
        reg = client.searches.register()
        tj = client.searches.tilejson(reg.id, "WebMercatorQuad")
        assert isinstance(tj, TileJSON)
        assert len(tj.tiles) >= 1
        assert "WebMercatorQuad" in tj.tiles[0]
