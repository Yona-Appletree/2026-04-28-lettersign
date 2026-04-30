"""Tests for centerline marker detection."""

from __future__ import annotations

from shapely.geometry import GeometryCollection, LineString, MultiLineString

from lettersign.config import PREVIEW_MARKER_RADIUS_MM
from lettersign.markers import detect_markers


def test_linestring_endpoints() -> None:
    g = LineString([(0, 0), (10, 0)])
    markers = detect_markers(g)
    assert len(markers) == 2
    positions = {(m.position.x, m.position.y) for m in markers}
    assert positions == {(0, 0), (10, 0)}
    for m in markers:
        assert m.kind == "endpoint"
        assert m.radius_mm == PREVIEW_MARKER_RADIUS_MM == 5.0


def test_t_junction_branch_point_is_intersection() -> None:
    mls = MultiLineString(
        [
            ((0, 0), (5, 0)),
            ((5, 0), (5, 10)),
            ((5, 0), (10, 0)),
        ]
    )
    markers = detect_markers(mls)
    by_pos = {(m.position.x, m.position.y): m for m in markers}
    assert len(by_pos) == 4
    junction = by_pos[(5, 0)]
    assert junction.kind == "intersection"
    assert junction.radius_mm == PREVIEW_MARKER_RADIUS_MM
    assert by_pos[(0, 0)].kind == "endpoint"
    assert by_pos[(5, 10)].kind == "endpoint"
    assert by_pos[(10, 0)].kind == "endpoint"


def test_coincident_endpoints_deduped() -> None:
    """Two line parts meeting at one point (valence 2) yield a single marker there."""
    mls = MultiLineString(
        [
            ((0, 0), (2, 0)),
            ((2, 0), (4, 0)),
        ]
    )
    markers = detect_markers(mls)
    positions = {(m.position.x, m.position.y) for m in markers}
    assert positions == {(0, 0), (2, 0), (4, 0)}
    assert len(markers) == 3


def test_interior_crossing_yields_intersection() -> None:
    h = LineString([(0, 5), (10, 5)])
    v = LineString([(5, 0), (5, 10)])
    markers = detect_markers(GeometryCollection([h, v]))
    kinds_at = {(m.position.x, m.position.y): m.kind for m in markers}
    assert kinds_at[(5, 5)] == "intersection"
