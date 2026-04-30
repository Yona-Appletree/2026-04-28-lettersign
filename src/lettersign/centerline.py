#!/usr/bin/env python3
"""
Approximate centerlines for filled SVG paths using Shapely and pygeoops.

The legacy CLI renders a debug SVG (filled outline plus smoothed centerline).
Project builds call ``generate_centerline_geometry`` with normalized ``SvgInput``.

Examples (legacy): ``uv run lettersign Y.svg``, ``uv run lettersign --preset fast Y.svg``.
"""

from __future__ import annotations

import argparse
import math
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import pygeoops
from shapely.geometry import GeometryCollection, LineString, MultiLineString, MultiPolygon, Polygon
from shapely.ops import unary_union
from svgpathtools import svg2paths2

from lettersign.geometry import SvgInput

RenderableSvgGeometry = Polygon | MultiPolygon | LineString | MultiLineString | GeometryCollection


@dataclass(frozen=True)
class CenterlineGeometry:
    """Filled outline and medial-axis centerline in millimeter coordinates."""

    outline: Polygon | MultiPolygon
    centerline: LineString | MultiLineString | GeometryCollection


def generate_centerline_geometry(
    svg_input: SvgInput,
    *,
    densify_distance: float,
    min_branch_length: float,
    simplify: float,
    split_components: bool = True,
    verbose: bool = False,
) -> CenterlineGeometry:
    """Build unioned outline from normalized paths and compute pygeoops centerline."""
    rings: list[list[tuple[float, float]]] = []
    for source in svg_input.source_paths:
        for ring in source.rings:
            if len(ring) < 4:
                continue
            rings.append([(p.x, p.y) for p in ring])
    if not rings:
        msg = (
            "SvgInput has no closed rings with enough sampled points to build a filled shape "
            f"(from {svg_input.path})"
        )
        raise ValueError(msg)
    outline = build_shape_from_nested_rings(rings)
    centerline = compute_centerline(
        outline,
        densify_distance=densify_distance,
        min_branch_length=min_branch_length,
        simplify=simplify,
        split_components=split_components,
        verbose=verbose,
    )
    return CenterlineGeometry(outline=outline, centerline=centerline)


def run_centerline(args: argparse.Namespace) -> None:
    """Run centerline generation from a populated argparse namespace (preset applied)."""
    apply_preset(args)
    svg_path = Path(args.svg)
    output_path = args.output or svg_path.with_name(f"{svg_path.stem}.centerline.svg")

    started_at = time.perf_counter()
    log(args.verbose, f"Reading viewBox from {svg_path}")
    view_box = read_view_box(svg_path)
    log(args.verbose, f"Loading SVG paths with flatness={args.flatness:g}")
    shape = load_filled_shape(svg_path, flatness=args.flatness, verbose=args.verbose)
    if args.input_simplify > 0:
        log(args.verbose, f"Simplifying input polygons by {args.input_simplify:g}")
        shape = shape.simplify(args.input_simplify, preserve_topology=True)
    log(args.verbose, "Computing centerline")
    centerline_geom = compute_centerline(
        shape,
        densify_distance=args.densify_distance,
        min_branch_length=args.min_branch_length,
        simplify=args.simplify,
        split_components=not args.no_split_components,
        verbose=args.verbose,
    )

    log(args.verbose, "Rendering debug SVG")
    output_path.write_text(
        render_debug_svg(
            view_box,
            shape,
            centerline_geom,
            use_bezier=not args.no_bezier,
            bezier_tension=args.bezier_tension,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")
    print(f"Shape area: {shape.area:.1f}")
    print(f"Centerline length: {centerline_geom.length:.1f}")
    print(f"Elapsed: {time.perf_counter() - started_at:.2f}s")


def main() -> None:
    run_centerline(parse_args())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", nargs="?", default="Y.svg", help="Input SVG file.")
    parser.add_argument("-o", "--output", type=Path, help="Output debug SVG path.")
    parser.add_argument(
        "--preset",
        choices=["fast", "default", "high"],
        default="default",
        help="Convenience quality/speed preset. Explicit numeric flags override the preset.",
    )
    parser.add_argument(
        "--flatness",
        type=float,
        default=None,
        help="Approximate SVG curves with points about this many SVG units apart.",
    )
    parser.add_argument(
        "--densify-distance",
        type=float,
        default=None,
        help="pygeoops centerline densification distance. Smaller can preserve more detail.",
    )
    parser.add_argument(
        "--min-branch-length",
        type=float,
        default=20.0,
        help="Prune centerline branches shorter than this many SVG units.",
    )
    parser.add_argument(
        "--simplify",
        type=float,
        default=None,
        help="Simplify centerline by this many SVG units. Use 0 to disable.",
    )
    parser.add_argument(
        "--input-simplify",
        type=float,
        default=None,
        help="Simplify the filled shape before centerline generation. Helps a lot for text.",
    )
    parser.add_argument(
        "--no-bezier",
        action="store_true",
        help="Render centerline as straight polyline segments instead of cubic Beziers.",
    )
    parser.add_argument(
        "--bezier-tension",
        type=float,
        default=1.0,
        help="Catmull-Rom to Bezier tension. Lower values are flatter; 1.0 is a smooth default.",
    )
    parser.add_argument(
        "--no-split-components",
        action="store_true",
        help="Process the whole shape at once instead of one disconnected component at a time.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print per-component progress.")
    return parser.parse_args()


def apply_preset(args: argparse.Namespace) -> None:
    presets = {
        "fast": {
            "flatness": 2.0,
            "densify_distance": 12.0,
            "simplify": 2.0,
            "input_simplify": 1.0,
        },
        "default": {
            "flatness": 1.0,
            "densify_distance": 6.0,
            "simplify": 1.0,
            "input_simplify": 0.5,
        },
        "high": {
            "flatness": 0.5,
            "densify_distance": 4.0,
            "simplify": 0.5,
            "input_simplify": 0.0,
        },
    }

    for name, value in presets[args.preset].items():
        if getattr(args, name) is None:
            setattr(args, name, value)


def load_filled_shape(svg_path: Path, flatness: float, verbose: bool) -> Polygon | MultiPolygon:
    paths, _attributes, _svg_attributes = svg2paths2(str(svg_path))
    rings = []

    log(verbose, f"Found {len(paths)} SVG path element(s)")
    for path_index, path in enumerate(paths, start=1):
        subpaths = path.continuous_subpaths()
        log(verbose, f"Flattening path {path_index}/{len(paths)} with {len(subpaths)} contour(s)")
        for subpath_index, subpath in enumerate(subpaths, start=1):
            points = flatten_subpath(subpath, flatness=flatness)
            log(
                verbose,
                f"  contour {subpath_index}/{len(subpaths)}: "
                f"{len(subpath)} segment(s), {len(points)} sampled point(s)",
            )
            if len(points) >= 4:
                rings.append(points)

    if not rings:
        raise ValueError(f"No closed filled contours found in {svg_path}")

    log(verbose, f"Building polygons from {len(rings)} contour(s)")
    return build_shape_from_nested_rings(rings)


def flatten_subpath(subpath: Any, flatness: float) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for segment in subpath:
        segment_length = estimate_segment_length(segment)
        sample_count = max(1, math.ceil(segment_length / flatness))
        for index in range(sample_count):
            append_unique(points, complex_to_xy(segment.point(index / sample_count)))

    append_unique(points, complex_to_xy(subpath[-1].point(1.0)))
    if points and points[0] != points[-1]:
        points.append(points[0])
    return points


def estimate_segment_length(segment: Any, samples: int = 8) -> float:
    previous = complex_to_xy(segment.point(0.0))
    total = 0.0
    for index in range(1, samples + 1):
        current = complex_to_xy(segment.point(index / samples))
        total += distance(previous, current)
        previous = current
    return total


def build_shape_from_nested_rings(
    rings: Iterable[list[tuple[float, float]]],
) -> Polygon | MultiPolygon:
    ring_polygons = [Polygon(ring).buffer(0) for ring in rings]
    ring_polygons = [
        polygon for polygon in ring_polygons if not polygon.is_empty and polygon.area > 0
    ]

    if not ring_polygons:
        raise ValueError("SVG contours did not produce any valid polygons")

    parent_by_index: dict[int, int | None] = {}
    for index, polygon in enumerate(ring_polygons):
        min_parent_area = polygon.area + 1e-9
        containing = [
            (other_index, other.area)
            for other_index, other in enumerate(ring_polygons)
            if (
                other_index != index
                and other.area > min_parent_area
                and other.contains(polygon.representative_point())
            )
        ]
        parent_by_index[index] = (
            min(containing, key=lambda item: item[1])[0] if containing else None
        )

    polygons = []
    for index, polygon in enumerate(ring_polygons):
        if nesting_depth(index, parent_by_index) % 2 != 0:
            continue

        holes = [
            ring_polygons[hole_index].exterior.coords
            for hole_index, parent_index in parent_by_index.items()
            if parent_index == index and nesting_depth(hole_index, parent_by_index) % 2 == 1
        ]
        polygons.append(Polygon(polygon.exterior.coords, holes))

    shape = unary_union(polygons).buffer(0)
    if not isinstance(shape, (Polygon, MultiPolygon)):
        raise ValueError(f"Expected a polygonal shape, got {shape.geom_type}")
    return shape


def compute_centerline(
    shape: Polygon | MultiPolygon,
    densify_distance: float,
    min_branch_length: float,
    simplify: float,
    split_components: bool,
    verbose: bool,
) -> LineString | MultiLineString | GeometryCollection:
    if split_components:
        lines = []
        polygons = list_polygon_parts(shape)
        for index, polygon in enumerate(polygons, start=1):
            if verbose:
                print(
                    f"Centerline component {index}/{len(polygons)}: "
                    f"area={polygon.area:.1f}, bounds={format_bounds(polygon.bounds)}"
                )
            line = compute_single_centerline(
                polygon,
                densify_distance=densify_distance,
                min_branch_length=min_branch_length,
                simplify=simplify,
            )
            if not line.is_empty:
                lines.extend(line.geoms if isinstance(line, MultiLineString) else [line])
        centerline = MultiLineString(lines)
    else:
        centerline = compute_single_centerline(
            shape,
            densify_distance=densify_distance,
            min_branch_length=min_branch_length,
            simplify=simplify,
        )

    if centerline.is_empty:
        raise ValueError("Centerline generation produced an empty result")
    return centerline


def compute_single_centerline(
    shape: Polygon | MultiPolygon,
    densify_distance: float,
    min_branch_length: float,
    simplify: float,
) -> LineString | MultiLineString | GeometryCollection:
    try:
        centerline = pygeoops.centerline(
            shape,
            densify_distance=densify_distance,
            min_branch_length=min_branch_length,
            simplifytolerance=simplify,
            extend=False,
        )
    except TypeError:
        centerline = pygeoops.centerline(shape)
        if simplify > 0:
            centerline = centerline.simplify(simplify)

    return centerline


def list_polygon_parts(shape: Polygon | MultiPolygon) -> list[Polygon]:
    if isinstance(shape, Polygon):
        return [shape]
    return list(shape.geoms)


def render_debug_svg(
    view_box: tuple[float, float, float, float],
    shape: Polygon | MultiPolygon,
    centerline: LineString | MultiLineString | GeometryCollection,
    use_bezier: bool,
    bezier_tension: float,
) -> str:
    min_x, min_y, width, height = view_box
    shape_path = geometry_to_svg_path(shape)
    centerline_path = geometry_to_svg_path(
        centerline,
        smooth_lines=use_bezier,
        bezier_tension=bezier_tension,
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x:g} {min_y:g} {width:g} {height:g}">
  <path d="{shape_path}" fill="#231f20" fill-opacity="0.18" stroke="#231f20" stroke-width="2"/>
  <path d="{centerline_path}" fill="none" stroke="#ff2d55" stroke-width="8"
    stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def geometry_to_svg_path(
    geometry: RenderableSvgGeometry,
    smooth_lines: bool = False,
    bezier_tension: float = 1.0,
) -> str:
    if isinstance(geometry, Polygon):
        return polygon_to_svg_path(geometry)
    if isinstance(geometry, MultiPolygon):
        return " ".join(polygon_to_svg_path(polygon) for polygon in geometry.geoms)
    if isinstance(geometry, LineString):
        return linestring_to_svg_path(geometry, smooth=smooth_lines, bezier_tension=bezier_tension)
    if isinstance(geometry, MultiLineString):
        return " ".join(
            linestring_to_svg_path(line, smooth=smooth_lines, bezier_tension=bezier_tension)
            for line in geometry.geoms
        )
    if isinstance(geometry, GeometryCollection):
        return " ".join(
            geometry_to_svg_path(part, smooth_lines=smooth_lines, bezier_tension=bezier_tension)
            for part in geometry.geoms
        )
    raise TypeError(f"Cannot render {geometry.geom_type} as an SVG path")


def polygon_to_svg_path(polygon: Polygon) -> str:
    parts = [ring_to_svg_path(polygon.exterior.coords, close=True)]
    parts.extend(ring_to_svg_path(interior.coords, close=True) for interior in polygon.interiors)
    return " ".join(parts)


def linestring_to_svg_path(line: LineString, smooth: bool, bezier_tension: float) -> str:
    coords = list(line.coords)
    if smooth:
        return catmull_rom_to_bezier_path(coords, tension=bezier_tension)
    return ring_to_svg_path(coords, close=False)


def ring_to_svg_path(coords, close: bool) -> str:
    coords = list(coords)
    if not coords:
        return ""
    commands = [f"M {coords[0][0]:.3f} {coords[0][1]:.3f}"]
    commands.extend(f"L {x:.3f} {y:.3f}" for x, y in coords[1:])
    if close:
        commands.append("Z")
    return " ".join(commands)


def catmull_rom_to_bezier_path(coords, tension: float) -> str:
    points = [tuple(coord[:2]) for coord in coords]
    if len(points) < 3:
        return ring_to_svg_path(points, close=False)

    commands = [f"M {points[0][0]:.3f} {points[0][1]:.3f}"]
    tension = max(0.0, tension)

    for index in range(len(points) - 1):
        p0 = points[max(index - 1, 0)]
        p1 = points[index]
        p2 = points[index + 1]
        p3 = points[min(index + 2, len(points) - 1)]

        c1 = add_points(p1, scale_point(subtract_points(p2, p0), tension / 6.0))
        c2 = subtract_points(p2, scale_point(subtract_points(p3, p1), tension / 6.0))
        commands.append(
            f"C {c1[0]:.3f} {c1[1]:.3f}, {c2[0]:.3f} {c2[1]:.3f}, {p2[0]:.3f} {p2[1]:.3f}"
        )

    return " ".join(commands)


def read_view_box(svg_path: Path) -> tuple[float, float, float, float]:
    root = ElementTree.parse(svg_path).getroot()
    view_box = root.attrib.get("viewBox")
    if view_box:
        values = [float(value) for value in re.split(r"[,\s]+", view_box.strip()) if value]
        if len(values) == 4:
            return values[0], values[1], values[2], values[3]
    return 0.0, 0.0, 1000.0, 1000.0


def format_bounds(bounds: tuple[float, float, float, float]) -> str:
    min_x, min_y, max_x, max_y = bounds
    return f"{min_x:.1f},{min_y:.1f} {max_x:.1f},{max_y:.1f}"


def log(verbose: bool, message: str) -> None:
    if verbose:
        print(message, flush=True)


def nesting_depth(index: int, parent_by_index: dict[int, int | None]) -> int:
    depth = 0
    parent = parent_by_index[index]
    seen = {index}
    while parent is not None:
        if parent in seen:
            cycle = " -> ".join(str(item) for item in [*seen, parent])
            raise ValueError(f"Cycle detected in SVG contour nesting: {cycle}")
        seen.add(parent)
        depth += 1
        parent = parent_by_index[parent]
    return depth


def append_unique(points: list[tuple[float, float]], point: tuple[float, float]) -> None:
    if not points or distance(points[-1], point) > 1e-9:
        points.append(point)


def add_points(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] + b[0], a[1] + b[1]


def subtract_points(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] - b[0], a[1] - b[1]


def scale_point(point: tuple[float, float], scale: float) -> tuple[float, float]:
    return point[0] * scale, point[1] * scale


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def complex_to_xy(point: complex) -> tuple[float, float]:
    return point.real, point.imag


if __name__ == "__main__":
    main()
