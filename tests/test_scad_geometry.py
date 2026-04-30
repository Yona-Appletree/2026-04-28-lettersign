"""Tests for SCAD geometry model construction (Shapely clipping and filtering)."""

from __future__ import annotations

from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

from lettersign.config import PREVIEW_MARKER_RADIUS_MM, ProjectConfig
from lettersign.geometry import Bounds, Marker, Point, SourcePath, SvgInput
from lettersign.scad_geometry import ScadModel, build_scad_model


def _rect_source(name: str = "path1") -> SourcePath:
    ring = (
        Point(0.0, 0.0),
        Point(100.0, 0.0),
        Point(100.0, 100.0),
        Point(0.0, 100.0),
        Point(0.0, 0.0),
    )
    return SourcePath(name=name, rings=(ring,))


def _svg_input(*paths: SourcePath) -> SvgInput:
    xs = [p.x for sp in paths for ring in sp.rings for p in ring]
    ys = [p.y for sp in paths for ring in sp.rings for p in ring]
    return SvgInput(
        path=Path("test.svg"),
        view_box=(0.0, 0.0, 100.0, 100.0),
        unit_scale_mm=1.0,
        bounds=Bounds(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys)),
        source_paths=tuple(paths),
    )


def test_single_source_path_path1_outline_and_channels() -> None:
    src = _rect_source()
    svg = _svg_input(src)
    path_shape = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    outline = path_shape
    centerline = LineString([(10.0, 50.0), (90.0, 50.0)])
    config = ProjectConfig(led_channel_width=10.0, post_height=7.0, line_resolution=0.5)

    model = build_scad_model(
        project_name="demo",
        svg_input=svg,
        outline=outline,
        centerline=centerline,
        markers=(),
        config=config,
    )

    assert len(model.parts) == 1
    part = model.parts[0]
    assert part.name == "path1"
    assert len(part.outline.points) >= 4
    assert len(part.outline.paths) >= 1
    assert len(part.channels) >= 1
    ch = part.channels[0]
    assert len(ch.points) >= 3
    assert len(ch.paths) >= 1


def test_marker_inside_becomes_post_outside_excluded() -> None:
    src = _rect_source()
    svg = _svg_input(src)
    outline = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    centerline = LineString([(10.0, 50.0), (90.0, 50.0)])
    markers = (
        Marker(position=Point(50.0, 50.0), radius_mm=PREVIEW_MARKER_RADIUS_MM),
        Marker(position=Point(500.0, 500.0), radius_mm=PREVIEW_MARKER_RADIUS_MM),
    )
    custom_height = 22.5
    config = ProjectConfig(post_height=custom_height, led_channel_width=4.0)

    model = build_scad_model(
        project_name="demo",
        svg_input=svg,
        outline=outline,
        centerline=centerline,
        markers=markers,
        config=config,
    )

    part = model.parts[0]
    assert len(part.posts) == 1
    post = part.posts[0]
    assert post.position == Point(50.0, 50.0)
    assert post.radius_mm == PREVIEW_MARKER_RADIUS_MM
    assert post.height_mm == custom_height


def test_config_led_channel_width_and_empty_channel_does_not_crash() -> None:
    src = _rect_source()
    svg = _svg_input(src)
    outline = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    # Horizontal strip entirely above the rectangle - no overlap with outline
    centerline = LineString([(0.0, 200.0), (100.0, 200.0)])
    custom_width = 6.5
    config = ProjectConfig(led_channel_width=custom_width)

    model = build_scad_model(
        project_name="demo",
        svg_input=svg,
        outline=outline,
        centerline=centerline,
        markers=(),
        config=config,
    )

    assert model.led_channel_width_mm == custom_width
    assert model.parts[0].channels == ()


def test_model_dimensions_from_config() -> None:
    src = _rect_source()
    svg = _svg_input(src)
    outline = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    centerline = LineString([(50.0, 10.0), (50.0, 90.0)])
    cfg = ProjectConfig(height=20.0, led_channel_width=3.0, post_height=11.0, line_resolution=0.25)

    model = build_scad_model(
        project_name="foo",
        svg_input=svg,
        outline=outline,
        centerline=centerline,
        markers=(),
        config=cfg,
    )

    assert isinstance(model, ScadModel)
    assert model.project_name == "foo"
    assert model.height_mm == cfg.height
    assert model.led_channel_width_mm == cfg.led_channel_width
    assert model.post_height_mm == cfg.post_height


def test_union_outline_two_paths() -> None:
    """Outline argument matches pipeline union while parts stay per-source."""
    a = SourcePath(
        "path1",
        ((Point(0, 0), Point(40, 0), Point(40, 40), Point(0, 40), Point(0, 0)),),
    )
    b = SourcePath(
        "path2",
        ((Point(60, 0), Point(100, 0), Point(100, 40), Point(60, 40), Point(60, 0)),),
    )
    svg = _svg_input(a, b)
    poly_a = Polygon([(0, 0), (40, 0), (40, 40), (0, 40)])
    poly_b = Polygon([(60, 0), (100, 0), (100, 40), (60, 40)])
    outline = unary_union([poly_a, poly_b])
    assert isinstance(outline, MultiPolygon)
    centerline = LineString([(20.0, 20.0), (80.0, 20.0)])
    model = build_scad_model(
        project_name="two",
        svg_input=svg,
        outline=outline,
        centerline=centerline,
        markers=(),
        config=ProjectConfig(led_channel_width=8.0),
    )
    assert [p.name for p in model.parts] == ["path1", "path2"]
    assert all(len(p.outline.paths) >= 1 for p in model.parts)
    assert all(len(p.channels) >= 1 for p in model.parts)
