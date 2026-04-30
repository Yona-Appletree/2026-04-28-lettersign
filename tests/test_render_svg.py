"""Structural tests for normalized centerline SVG rendering."""

from __future__ import annotations

from xml.etree import ElementTree

from shapely.geometry import LineString, Polygon

from lettersign.config import PREVIEW_MARKER_RADIUS_MM, ProjectConfig
from lettersign.geometry import Marker, Point
from lettersign.render_svg import GENERATED_FILE_COMMENT, render_centerline_svg


def _svg_elements(root: ElementTree.Element, local_name: str) -> list[ElementTree.Element]:
    suffix = f"}}{local_name}"
    return [el for el in root.iter() if el.tag == local_name or el.tag.endswith(suffix)]


def test_render_centerline_svg_structure() -> None:
    outline = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    centerline = LineString([(10, 20), (90, 70)])
    markers = (Marker(position=Point(50.0, 25.0), radius_mm=PREVIEW_MARKER_RADIUS_MM),)
    cfg = ProjectConfig()

    svg = render_centerline_svg(
        view_box=(0, 0, 100, 100),
        outlines=outline,
        centerline=centerline,
        markers=markers,
        led_channel_width=cfg.led_channel_width,
    )

    assert svg.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert f"<!-- {GENERATED_FILE_COMMENT}" in svg

    root = ElementTree.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "viewBox" in root.attrib

    paths = _svg_elements(root, "path")
    assert len(paths) == 2

    outline_path, centerline_path = paths
    assert outline_path.get("fill") == "none"
    assert outline_path.get("stroke") in ("#000000", "black")
    assert outline_path.get("stroke-width") is not None

    assert centerline_path.get("fill") == "none"
    assert centerline_path.get("stroke") in ("#ff0000", "red")
    assert centerline_path.get("d") == "M 10.000 80.000 L 90.000 30.000"
    assert float(centerline_path.get("stroke-width", "0")) == cfg.led_channel_width
    assert centerline_path.get("stroke-linecap") == "round"
    assert centerline_path.get("stroke-linejoin") == "round"

    circles = _svg_elements(root, "circle")
    assert len(circles) == 1
    circle = circles[0]
    assert float(circle.get("r", "0")) == PREVIEW_MARKER_RADIUS_MM
    assert float(circle.get("cx", "0")) == 50.0
    assert float(circle.get("cy", "0")) == 75.0
    assert circle.get("fill") == "#008000"
    assert circle.get("stroke") == "#008000"

    for el in root.iter():
        assert "style" not in el.attrib
        assert "class" not in el.attrib
