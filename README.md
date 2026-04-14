# pytitiler

Python client for [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) — async-first with sync wrapper.

Covers all 78 endpoints across STAC searches, collections, items, algorithms, colormaps, and tiling schemes.

## Installation

```bash
pip install git+https://github.com/danghoangnhan/pytitiler.git
```

## Quick Start

### Sync

```python
from pytitiler import TiTilerPgSTAC

with TiTilerPgSTAC("http://localhost:8081") as client:
    # Register a STAC search
    result = client.searches.register(collections=["sentinel-2"])

    # Fetch a tile
    tile = client.searches.tile(result.id, "WebMercatorQuad", 10, 512, 384)

    # Get TileJSON
    tj = client.searches.tilejson(result.id, "WebMercatorQuad")

    # Query a point
    point = client.searches.point(result.id, 12.5, 45.3)

    # Get a bbox image
    img = client.searches.bbox_image(result.id, (10.0, 45.0, 11.0, 46.0), width=512, height=512)
```

### Async

```python
import asyncio
from pytitiler import AsyncTiTilerPgSTAC

async def main():
    async with AsyncTiTilerPgSTAC("http://localhost:8081") as client:
        result = await client.searches.register(collections=["sentinel-2"])
        tile = await client.searches.tile(result.id, "WebMercatorQuad", 10, 512, 384)

asyncio.run(main())
```

## API Coverage

| Sub-API | Prefix | Endpoints |
|---------|--------|-----------|
| `client.searches` | `/searches/{id}/` | register, list, tile, tilejson, point, bbox_image, feature_image, statistics, info, wmts, assets_for_tile/bbox/point |
| `client.collections` | `/collections/{id}/` | tile, tilejson, point, bbox_image, feature_image, statistics, info, wmts, assets_for_tile/bbox/point |
| `client.items` | `/collections/{cid}/items/{iid}/` | tile, tilejson, point, bbox_image, feature_image, statistics, info, info_geojson, wmts, preview, assets, asset_statistics, renders |
| `client.algorithms` | `/algorithms/` | list, get |
| `client.colormaps` | `/colorMaps/` | list, get |
| `client.tiling_schemes` | `/tileMatrixSets/` | list, get |
| Root | `/` | health, landing, conformance |

## Rendering Parameters

Use `TileParams` and `PgSTACParams` to control rendering and query behavior:

```python
from pytitiler.models import TileParams, PgSTACParams

tile = client.searches.tile(
    search_id, "WebMercatorQuad", 10, 512, 384,
    tile_params=TileParams(
        assets=["visual"],
        resampling="bilinear",
        rescale=["0,255"],
    ),
    pgstac_params=PgSTACParams(
        items_limit=50,
        time_limit=10,
    ),
)
```

`TileParams` controls rendering (band selection, resampling, colormap, rescale). `PgSTACParams` controls PgSTAC query behavior (scan limits, timeouts). They are separate because PgSTAC params only apply to search/collection endpoints, not individual items.

## Architecture

```
AsyncTiTilerPgSTAC
├── searches    → AsyncSearchAPI(RasterEndpointsMixin)
├── collections → AsyncCollectionAPI(RasterEndpointsMixin)
├── items       → AsyncItemAPI(RasterEndpointsMixin)
├── algorithms  → AsyncAlgorithmAPI
├── colormaps   → AsyncColorMapAPI
└── tiling_schemes → AsyncTilingSchemeAPI

TiTilerPgSTAC (sync wrapper)
└── Same interface, runs async methods via dedicated event loop
```

`RasterEndpointsMixin` provides shared tile/bbox/point/tilejson/info/statistics/wmts operations. Each sub-API delegates to the mixin with its URL prefix, adding only resource-specific endpoints.

## Requirements

- Python >= 3.11
- httpx >= 0.27
- pydantic >= 2.0

## Development

```bash
git clone https://github.com/danghoangnhan/pytitiler.git
cd pytitiler
uv sync
uv run pytest tests/test_client.py -v
```

## License

MIT
