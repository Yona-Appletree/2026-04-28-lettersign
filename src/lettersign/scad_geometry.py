"""Convert normalized SVG paths, centerlines, markers, and config into a SCAD model."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from shapely.geometry import CAP_STYLE, JOIN_STYLE, MultiPolygon, Polygon
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry.base import BaseGeometry

from lettersign.centerline import build_shape_from_nested_rings
from lettersign.config import ProjectConfig
from lettersign.geometry import Marker, Point, SourcePath, SvgInput


@dataclass(frozen=True)
class ScadPolygon:
    points: tuple[Point, ...]
    paths: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ScadPost:
    position: Point
    radius_mm: float
    height_mm: float


@dataclass(frozen=True)
class ScadPathPart:
    name: str
    outline: ScadPolygon
    channels: tuple[ScadPolygon, ...]
    posts: tuple[ScadPost, ...]


@dataclass(frozen=True)
class ScadModel:
    project_name: str
    height_mm: float
    led_channel_width_mm: float
    post_height_mm: float
    parts: tuple[ScadPathPart, ...]


def build_scad_model(
    *,
    project_name: str,
    svg_input: SvgInput,
    outline: Polygon | MultiPolygon,
    centerline: BaseGeometry,
    markers: Sequence[Marker],
    config: ProjectConfig,
) -> ScadModel:
    """Build a per-path SCAD geometry model from pipeline inputs.

    Per-path outlines come from ``svg_input.source_paths``. The global ``centerline``
    is buffered and clipped to each source outline (see milestone Q1). The passed
    ``outline`` is the union outline from centerline generation; it must be
    non-empty so callers catch bad pipeline state early.
    """
    if outline.is_empty:
        msg = "outline must be non-empty"
        raise ValueError(msg)
    if not isinstance(outline, (Polygon, MultiPolygon)):
        msg = f"outline must be a Polygon or MultiPolygon, got {type(outline).__name__}"
        raise TypeError(msg)

    half_width = config.led_channel_width / 2.0
    quad_segs = _buffer_quad_segs(config.led_channel_width, config.line_resolution)
    global_channel = centerline.buffer(
        half_width,
        cap_style=CAP_STYLE.round,
        join_style=JOIN_STYLE.round,
        quad_segs=quad_segs,
    )

    parts: list[ScadPathPart] = []
    for source in svg_input.source_paths:
        path_shape = _source_path_to_shape(source)
        outline_poly = _outline_shape_to_scad_polygon(path_shape)
        clipped = global_channel.intersection(path_shape)
        channel_polys = _polygonal_geometry_to_scad_polygons(clipped)
        posts = _markers_for_outline(markers, path_shape, config.post_height)
        parts.append(
            ScadPathPart(
                name=source.name,
                outline=outline_poly,
                channels=channel_polys,
                posts=posts,
            )
        )

    return ScadModel(
        project_name=project_name,
        height_mm=config.height,
        led_channel_width_mm=config.led_channel_width,
        post_height_mm=config.post_height,
        parts=tuple(parts),
    )


def _buffer_quad_segs(led_channel_width_mm: float, line_resolution_mm: float) -> int:
    half = led_channel_width_mm / 2.0
    return max(4, min(32, math.ceil(half / line_resolution_mm)))


def _source_path_to_shape(source: SourcePath) -> Polygon | MultiPolygon:
    rings: list[list[tuple[float, float]]] = []
    for ring in source.rings:
        if len(ring) < 4:
            continue
        rings.append([(p.x, p.y) for p in ring])
    if not rings:
        msg = f"{source.name!r} has no closed rings with enough points to build a shape"
        raise ValueError(msg)
    return build_shape_from_nested_rings(rings)


def _ring_coords_to_points_and_path(
    ring_coords: Sequence[tuple[float, float]],
    points_out: list[Point],
) -> tuple[int, ...] | None:
    coords = list(ring_coords)
    if len(coords) >= 2 and coords[0] == coords[-1]:
        coords = coords[:-1]
    if len(coords) < 3:
        return None
    start = len(points_out)
    for x, y in coords:
        points_out.append(Point(x, y))
    return tuple(range(start, len(points_out)))


def _single_polygon_to_scad(poly: Polygon) -> ScadPolygon:
    points: list[Point] = []
    paths: list[tuple[int, ...]] = []
    exterior = _ring_coords_to_points_and_path(poly.exterior.coords, points)
    if exterior is None:
        msg = "polygon exterior did not yield a valid closed path"
        raise ValueError(msg)
    paths.append(exterior)
    for interior in poly.interiors:
        hole = _ring_coords_to_points_and_path(interior.coords, points)
        if hole is not None:
            paths.append(hole)
    return ScadPolygon(points=tuple(points), paths=tuple(paths))


def _merge_scad_polygons(parts: Sequence[ScadPolygon]) -> ScadPolygon:
    all_points: list[Point] = []
    all_paths: list[tuple[int, ...]] = []
    for part in parts:
        offset = len(all_points)
        all_points.extend(part.points)
        for path in part.paths:
            all_paths.append(tuple(i + offset for i in path))
    return ScadPolygon(points=tuple(all_points), paths=tuple(all_paths))


def _outline_shape_to_scad_polygon(shape: Polygon | MultiPolygon) -> ScadPolygon:
    if isinstance(shape, Polygon):
        return _single_polygon_to_scad(shape)
    sub = [_single_polygon_to_scad(p) for p in shape.geoms if not p.is_empty]
    if not sub:
        msg = "multipolygon outline had no non-empty parts"
        raise ValueError(msg)
    return _merge_scad_polygons(sub)


def _polygonal_geometry_to_scad_polygons(geom: BaseGeometry) -> tuple[ScadPolygon, ...]:
    if geom.is_empty:
        return ()
    gt = geom.geom_type
    if gt == "Polygon":
        return (_single_polygon_to_scad(geom),)
    if gt == "MultiPolygon":
        return tuple(_single_polygon_to_scad(p) for p in geom.geoms if not p.is_empty)
    if gt == "GeometryCollection":
        out: list[ScadPolygon] = []
        for g in geom.geoms:
            out.extend(_polygonal_geometry_to_scad_polygons(g))
        return tuple(out)
    return ()


def _markers_for_outline(
    markers: Sequence[Marker],
    outline_shape: Polygon | MultiPolygon,
    post_height_mm: float,
) -> tuple[ScadPost, ...]:
    posts: list[ScadPost] = []
    prepared = outline_shape.buffer(0)
    for marker in markers:
        pt = ShapelyPoint(marker.position.x, marker.position.y)
        if prepared.intersects(pt):
            posts.append(
                ScadPost(
                    position=marker.position,
                    radius_mm=marker.radius_mm,
                    height_mm=post_height_mm,
                )
            )
    return tuple(posts)
