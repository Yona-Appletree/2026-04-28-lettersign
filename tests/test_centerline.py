"""Tests for domain-driven centerline generation (SvgInput → Shapely)."""

from __future__ import annotations

from pathlib import Path

from lettersign.centerline import generate_centerline_geometry
from lettersign.svg_input import load_svg_input


def test_generate_centerline_geometry_square_positive_area_and_non_empty_line(
    tmp_path: Path,
) -> None:
    svg = tmp_path / "square.svg"
    svg.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<path d="M 10 10 L 90 10 L 90 90 L 10 90 Z"/>'
        "</svg>",
        encoding="utf-8",
    )
    svg_input = load_svg_input(svg, line_resolution=1.0)
    result = generate_centerline_geometry(
        svg_input,
        densify_distance=6.0,
        min_branch_length=20.0,
        simplify=1.0,
    )
    assert result.outline.area > 0
    assert not result.centerline.is_empty
    assert result.centerline.length > 0
