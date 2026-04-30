"""Project build orchestration: normalized SVG input through centerline preview."""

from __future__ import annotations

from pathlib import Path

from lettersign.centerline import generate_centerline_geometry
from lettersign.config import ProjectConfig
from lettersign.errors import InvalidSvgInputError
from lettersign.geometry import SvgInput
from lettersign.markers import detect_markers
from lettersign.project import ProjectPaths
from lettersign.render_scad import write_scad_outputs
from lettersign.render_svg import render_centerline_svg
from lettersign.scad_geometry import build_scad_model
from lettersign.svg_input import load_svg_input

# Align with legacy `lettersign.centerline` default preset tuning (millimeter space).
_PIPELINE_DENSIFY_DISTANCE_MM = 6.0
_PIPELINE_MIN_BRANCH_LENGTH_MM = 20.0
_PIPELINE_SIMPLIFY_MM = 1.0


def _normalized_view_box_mm(svg_input: SvgInput) -> tuple[float, float, float, float]:
    """View box in mm matching `svg_input.load_svg_input` lower-left coordinates."""
    _, _, vw, vh = svg_input.view_box
    width_mm = vw * svg_input.unit_scale_mm
    height_mm = vh * svg_input.unit_scale_mm
    return (0.0, 0.0, width_mm, height_mm)


def build_centerline_preview(paths: ProjectPaths, config: ProjectConfig) -> Path:
    """Load project SVG, compute geometry, write normalized centerline SVG and SCAD artifacts.

    Caller must ensure ``paths.input_svg`` exists (``cli.cmd_build`` checks first).
    """
    try:
        svg_input = load_svg_input(paths.input_svg, line_resolution=config.line_resolution)
    except ValueError as e:
        raise InvalidSvgInputError(str(e)) from e

    try:
        geom = generate_centerline_geometry(
            svg_input,
            densify_distance=_PIPELINE_DENSIFY_DISTANCE_MM,
            min_branch_length=_PIPELINE_MIN_BRANCH_LENGTH_MM,
            simplify=_PIPELINE_SIMPLIFY_MM,
            split_components=True,
            verbose=False,
        )
    except ValueError as e:
        raise InvalidSvgInputError(str(e)) from e

    markers = detect_markers(geom.centerline)
    view_box = _normalized_view_box_mm(svg_input)

    svg_text = render_centerline_svg(
        view_box=view_box,
        outlines=geom.outline,
        centerline=geom.centerline,
        markers=markers,
        led_channel_width=config.led_channel_width,
    )

    model = build_scad_model(
        project_name=paths.project_dir.name,
        svg_input=svg_input,
        outline=geom.outline,
        centerline=geom.centerline,
        markers=markers,
        config=config,
    )

    paths.centerline_svg.parent.mkdir(parents=True, exist_ok=True)
    paths.centerline_svg.write_text(svg_text, encoding="utf-8")
    write_scad_outputs(paths, model)
    return paths.centerline_svg
