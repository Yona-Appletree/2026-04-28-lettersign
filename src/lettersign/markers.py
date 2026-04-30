"""Centerline endpoint and intersection marker detection."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence

from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from lettersign.config import PREVIEW_MARKER_RADIUS_MM
from lettersign.geometry import Marker, Point


def detect_markers(
    centerline: BaseGeometry,
    *,
    tolerance: float = 1e-6,
) -> tuple[Marker, ...]:
    """Find endpoint and branch/intersection markers on centerline linework.

    Endpoints come from the first/last vertex of each ``LineString`` part.
    Locations where three or more of those endpoints coincide (within
    ``tolerance``) are classified as intersections. Additionally, interior
    crossing points between two line parts (Shapely intersection is a point not
    at either line's endpoints) are intersections. Nearby candidates merge;
    ``intersection`` wins over ``endpoint``.
    """
    lines = list(_iter_linestrings(centerline))
    if not lines:
        return ()

    endpoints: list[tuple[float, float]] = []
    for ls in lines:
        endpoints.extend(_line_vertex_endpoints(ls))

    endpoint_clusters = _cluster_sorted_points(endpoints, tolerance)
    candidates: list[tuple[float, float, str]] = []
    for cl in endpoint_clusters:
        rep_x, rep_y = cl[0]
        kind: str = "intersection" if len(cl) >= 3 else "endpoint"
        candidates.append((rep_x, rep_y, kind))

    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            inter = lines[i].intersection(lines[j])
            for x, y in _extract_intersection_points(inter):
                if _is_interior_crossing(x, y, lines[i], lines[j], tolerance):
                    candidates.append((x, y, "intersection"))

    merged = _merge_marker_candidates(candidates, tolerance)
    return tuple(
        Marker(
            position=Point(x, y),
            radius_mm=PREVIEW_MARKER_RADIUS_MM,
            kind=kind,
        )
        for x, y, kind in merged
    )


def _line_vertex_endpoints(ls: LineString) -> list[tuple[float, float]]:
    coords = list(ls.coords)
    if len(coords) >= 2:
        return [(coords[0][0], coords[0][1]), (coords[-1][0], coords[-1][1])]
    if len(coords) == 1:
        return [(coords[0][0], coords[0][1])]
    return []


def _iter_linestrings(geom: BaseGeometry) -> Iterator[LineString]:
    if geom.is_empty:
        return
    gt = geom.geom_type
    if gt == "LineString":
        yield geom
    elif gt == "LinearRing":
        yield LineString(geom.coords)
    elif gt == "MultiLineString":
        for g in geom.geoms:
            yield from _iter_linestrings(g)
    elif gt == "GeometryCollection":
        for g in geom.geoms:
            yield from _iter_linestrings(g)


def _cluster_sorted_points(
    points: Sequence[tuple[float, float]],
    tolerance: float,
) -> list[list[tuple[float, float]]]:
    if not points:
        return []
    sorted_pts = sorted(points, key=lambda p: (p[0], p[1]))
    clusters: list[list[tuple[float, float]]] = []
    for p in sorted_pts:
        for cl in clusters:
            r = cl[0]
            if math.hypot(p[0] - r[0], p[1] - r[1]) <= tolerance:
                cl.append(p)
                break
        else:
            clusters.append([p])
    return clusters


def _merge_marker_candidates(
    candidates: Sequence[tuple[float, float, str]],
    tolerance: float,
) -> list[tuple[float, float, str]]:
    if not candidates:
        return []
    sorted_c = sorted(candidates, key=lambda t: (t[0], t[1], t[2]))
    clusters: list[list[tuple[float, float, str]]] = []
    for m in sorted_c:
        for cl in clusters:
            r = cl[0]
            if math.hypot(m[0] - r[0], m[1] - r[1]) <= tolerance:
                cl.append(m)
                break
        else:
            clusters.append([m])
    out: list[tuple[float, float, str]] = []
    for cl in clusters:
        x, y, _ = cl[0]
        kind = "intersection" if any(k == "intersection" for *_, k in cl) else "endpoint"
        out.append((x, y, kind))
    return sorted(out, key=lambda t: (t[0], t[1], t[2]))


def _extract_intersection_points(geom: BaseGeometry) -> list[tuple[float, float]]:
    if geom.is_empty:
        return []
    gt = geom.geom_type
    if gt == "Point":
        return [(geom.x, geom.y)]
    if gt == "MultiPoint":
        return [(g.x, g.y) for g in geom.geoms]
    if gt == "GeometryCollection":
        pts: list[tuple[float, float]] = []
        for g in geom.geoms:
            pts.extend(_extract_intersection_points(g))
        return pts
    return []


def _is_interior_crossing(
    x: float,
    y: float,
    a: LineString,
    b: LineString,
    tolerance: float,
) -> bool:
    for ls in (a, b):
        for ex, ey in _line_vertex_endpoints(ls):
            if math.hypot(x - ex, y - ey) <= tolerance:
                return False
    return True
