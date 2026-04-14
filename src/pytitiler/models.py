"""Pydantic models for the titiler-pgstac API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class ImageType(str, Enum):
    png = "png"
    npy = "npy"
    tif = "tif"
    tiff = "tiff"
    jpeg = "jpeg"
    jpg = "jpg"
    jp2 = "jp2"
    webp = "webp"
    pngraw = "pngraw"


class ResamplingMethod(str, Enum):
    nearest = "nearest"
    bilinear = "bilinear"
    cubic = "cubic"
    cubic_spline = "cubic_spline"
    lanczos = "lanczos"
    average = "average"
    mode = "mode"
    gauss = "gauss"
    rms = "rms"


class WarpResampling(str, Enum):
    """Superset of ResamplingMethod — used for reprojection."""

    nearest = "nearest"
    bilinear = "bilinear"
    cubic = "cubic"
    cubic_spline = "cubic_spline"
    lanczos = "lanczos"
    average = "average"
    mode = "mode"
    max = "max"
    min = "min"
    med = "med"
    q1 = "q1"
    q3 = "q3"
    sum = "sum"
    rms = "rms"


class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"


class MetadataType(str, Enum):
    mosaic = "mosaic"
    search = "search"


class NodataType(str, Enum):
    alpha = "Alpha"
    mask = "Mask"
    internal = "Internal"
    nodata = "Nodata"
    none = "None"


# ──────────────────────────────────────────────
# Shared parameter models
# ──────────────────────────────────────────────

class PgSTACParams(BaseModel):
    """PgSTAC query-control parameters."""

    scan_limit: int | None = None
    items_limit: int | None = None
    time_limit: int | None = None
    exitwhenfull: bool | None = None
    skipcovered: bool | None = None


class TileParams(BaseModel):
    """Common rendering parameters for tile / bbox / preview endpoints."""

    scale: int | None = None
    bidx: list[int] | None = None
    assets: list[str] | None = None
    expression: str | None = None
    asset_bidx: list[str] | None = None
    asset_as_band: bool | None = None
    nodata: float | str | None = None
    unscale: bool | None = None
    resampling: ResamplingMethod | None = None
    reproject: WarpResampling | None = None
    pixel_selection: str | None = None
    buffer: float | None = None
    padding: int | None = None
    algorithm: str | None = None
    algorithm_params: str | None = None
    colormap_name: str | None = None
    colormap: str | None = None
    rescale: list[str] | None = None
    color_formula: str | None = None
    return_mask: bool | None = None


class BboxParams(TileParams):
    """Extended parameters for bbox-image endpoints."""

    coord_crs: str | None = None
    dst_crs: str | None = None
    max_size: int | None = None


# ──────────────────────────────────────────────
# Request models
# ──────────────────────────────────────────────

class SortExtension(BaseModel):
    field: str
    direction: SortDirection


class MosaicMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: MetadataType = MetadataType.mosaic
    bounds: (
        tuple[float, float, float, float]
        | tuple[float, float, float, float, float, float]
        | None
    ) = None
    minzoom: int | None = None
    maxzoom: int | None = None
    name: str | None = None
    assets: list[str] | None = None
    defaults: dict | None = None


class RegisterMosaicRequest(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    collections: list[str] | None = None
    ids: list[str] | None = None
    bbox: (
        tuple[float, float, float, float]
        | tuple[float, float, float, float, float, float]
        | None
    ) = None
    intersects: dict | None = None  # GeoJSON geometry
    datetime: str | None = None
    query: dict | None = None
    sortby: list[SortExtension] | None = None
    filter: dict | None = None
    filter_lang: str | None = Field(None, alias="filter-lang")
    metadata: MosaicMetadata | None = None


# ──────────────────────────────────────────────
# Response models
# ──────────────────────────────────────────────

class Link(BaseModel):
    href: str
    rel: str
    type: str | None = None
    title: str | None = None
    templated: bool | None = None


class RegisterResponse(BaseModel):
    id: str
    links: list[Link] | None = None


class Search(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hash: str
    search: dict
    where: str | None = Field(None, alias="_where")
    orderby: str | None = None
    lastused: datetime
    usecount: int
    metadata: MosaicMetadata


class SearchInfo(BaseModel):
    search: Search
    links: list[Link] | None = None


class Context(BaseModel):
    returned: int
    limit: int | None = None
    matched: int | None = None


class SearchList(BaseModel):
    searches: list[SearchInfo]
    links: list[Link] | None = None
    context: Context


class TileJSON(BaseModel):
    model_config = ConfigDict(extra="allow")

    tilejson: str = "3.0.0"
    name: str | None = None
    description: str | None = None
    version: str = "1.0.0"
    attribution: str | None = None
    scheme: str = "xyz"
    tiles: list[str]
    minzoom: int = 0
    maxzoom: int = 30
    bounds: list[float] = [-180, -85.0511287798066, 180, 85.0511287798066]
    center: tuple[float, float, int] | None = None


class DatasetInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    bounds: tuple[float, float, float, float]
    crs: str
    band_metadata: list[tuple[str, dict]]
    band_descriptions: list[tuple[str, str]]
    dtype: str
    nodata_type: NodataType
    colorinterp: list[str] | None = None
    scales: list[float] | None = None
    offsets: list[float] | None = None


class AssetPoint(BaseModel):
    name: str
    values: list[float | None]
    band_names: list[str]
    band_descriptions: list[str] | None = None


class MosaicPointResponse(BaseModel):
    coordinates: list[float]
    assets: list[AssetPoint]


class PointResponse(BaseModel):
    coordinates: list[float]
    values: list[float | None]
    band_names: list[str]
    band_descriptions: list[str] | None = None


class BandStatistics(BaseModel):
    model_config = ConfigDict(extra="allow")

    min: float
    max: float
    mean: float
    count: float
    sum: float
    std: float
    median: float
    majority: float
    minority: float
    unique: float
    histogram: list[list[float | int]]
    valid_percent: float
    masked_pixels: float
    valid_pixels: float


class RenderItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    assets: list[str]
    title: str | None = None
    rescale: list[list[float]] | None = None
    nodata: float | None = None
    colormap_name: str | None = None
    colormap: dict | None = None
    color_formula: str | None = None
    resampling: str | None = None
    expression: str | None = None


class AlgorithmRef(BaseModel):
    id: str
    title: str | None = None
    links: list[Link] | None = None


class AlgorithmMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str | None = None
    description: str | None = None
    inputs: dict | None = None
    outputs: dict | None = None
    parameters: dict | None = None


class ColorMapRef(BaseModel):
    id: str
    title: str | None = None
    links: list[Link] | None = None


class TileMatrixSetRef(BaseModel):
    id: str
    title: str | None = None
    links: list[Link] | None = None
