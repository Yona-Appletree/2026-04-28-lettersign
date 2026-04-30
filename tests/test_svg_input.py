"""Tests for SVG input normalization and unit conversion."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import pytest

from lettersign.geometry import Point
from lettersign.svg_input import derive_unit_scale_mm, load_svg_input, parse_length_to_mm


def test_parse_length_to_mm_variants() -> None:
    assert parse_length_to_mm("100mm") == pytest.approx(100.0)
    assert parse_length_to_mm("2cm") == pytest.approx(20.0)
    assert parse_length_to_mm("1in") == pytest.approx(25.4)
    assert parse_length_to_mm("72pt") == pytest.approx(25.4)
    assert parse_length_to_mm("96px") == pytest.approx(25.4)
    assert parse_length_to_mm("100") is None
    assert parse_length_to_mm("50%") is None


def test_derive_unit_scale_mm_fallback_is_one() -> None:
    root = ElementTree.Element("svg", {"viewBox": "0 0 100 200"})
    _, _, vb_w, vb_h = (0.0, 0.0, 100.0, 200.0)
    assert derive_unit_scale_mm(root, (0.0, 0.0, vb_w, vb_h)) == pytest.approx(1.0)


def test_derive_unit_scale_mm_from_width_vs_viewbox() -> None:
    root = ElementTree.Element(
        "svg",
        {"viewBox": "0 0 200 100", "width": "100mm", "height": "100mm"},
    )
    # physical width / viewBox width => 0.5 mm per SVG unit (width preferred over height).
    assert derive_unit_scale_mm(root, (0.0, 0.0, 200.0, 100.0)) == pytest.approx(0.5)


def test_load_svg_input_unit_fallback_one_mm_per_unit(tmp_path: Path) -> None:
    svg = tmp_path / "square.svg"
    svg.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<path d="M 10 10 L 10 90 L 90 90 L 90 10 Z"/>'
        "</svg>",
        encoding="utf-8",
    )
    loaded = load_svg_input(svg, line_resolution=1.0)
    assert loaded.unit_scale_mm == pytest.approx(1.0)
    assert loaded.bounds.min_x == pytest.approx(10.0)
    assert loaded.bounds.min_y == pytest.approx(10.0)
    assert loaded.bounds.max_x == pytest.approx(90.0)
    assert loaded.bounds.max_y == pytest.approx(90.0)
    assert len(loaded.source_paths) == 1
    assert loaded.source_paths[0].name == "path1"
    ring0 = loaded.source_paths[0].rings[0]
    assert Point(10.0, 90.0) in ring0
    assert Point(90.0, 90.0) in ring0
    assert Point(90.0, 10.0) in ring0
    assert Point(10.0, 10.0) in ring0


def test_load_svg_input_physical_width_scales_coordinates(tmp_path: Path) -> None:
    svg = tmp_path / "scaled.svg"
    svg.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 200 100" width="100mm" height="50mm">'
        '<path d="M 0 0 L 200 0 L 200 100 L 0 100 Z"/>'
        "</svg>",
        encoding="utf-8",
    )
    loaded = load_svg_input(svg, line_resolution=1.0)
    assert loaded.unit_scale_mm == pytest.approx(0.5)
    assert loaded.bounds.max_x == pytest.approx(100.0)
    assert loaded.bounds.max_y == pytest.approx(50.0)


def test_load_svg_input_multiple_paths_named(tmp_path: Path) -> None:
    svg = tmp_path / "multi.svg"
    svg.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
        '<path d="M 0 0 L 20 0 L 20 20 L 0 20 Z"/>'
        '<path d="M 50 50 L 80 50 L 80 80 L 50 80 Z"/>'
        "</svg>",
        encoding="utf-8",
    )
    loaded = load_svg_input(svg, line_resolution=0.5)
    assert [sp.name for sp in loaded.source_paths] == ["path1", "path2"]
    assert len(loaded.source_paths[0].rings) >= 1
    assert len(loaded.source_paths[1].rings) >= 1
