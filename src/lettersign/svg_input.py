"""SVG metadata parsing, unit scaling, path flattening, and mm normalization."""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

from svgpathtools import svg2paths2

from lettersign.centerline import flatten_subpath
from lettersign.geometry import Bounds, Point, SourcePath, SvgInput

_LENGTH_RE = re.compile(
    r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*(mm|cm|in|pt|px)\s*$",
    re.IGNORECASE,
)


def load_svg_input(svg_path: Path, *, line_resolution: float) -> SvgInput:
    """Load SVG path geometry with lower-left mm coordinates and unit scaling."""
    tree = ElementTree.parse(svg_path)
    root = tree.getroot()
    view_box = _view_box_from_root(root)
    unit_scale_mm = derive_unit_scale_mm(root, view_box)
    flatness_svg = line_resolution / unit_scale_mm

    paths, _attributes, _svg_attributes = svg2paths2(str(svg_path))
    if not paths:
        msg = f"No <path> geometry found in {svg_path}"
        raise ValueError(msg)

    vb_min_x, vb_min_y, vb_w, vb_h = view_box

    def svg_to_mm(x: float, y: float) -> Point:
        x_mm = (x - vb_min_x) * unit_scale_mm
        y_mm = (vb_h - (y - vb_min_y)) * unit_scale_mm
        return Point(x_mm, y_mm)

    source_paths: list[SourcePath] = []
    all_mm_xy: list[tuple[float, float]] = []

    for path_index, path in enumerate(paths, start=1):
        rings_out: list[tuple[Point, ...]] = []
        for subpath in path.continuous_subpaths():
            sampled = flatten_subpath(subpath, flatness=flatness_svg)
            if len(sampled) < 4:
                continue
            ring = tuple(svg_to_mm(x, y) for x, y in sampled)
            rings_out.append(ring)
            all_mm_xy.extend((p.x, p.y) for p in ring)
        source_paths.append(SourcePath(name=f"path{path_index}", rings=tuple(rings_out)))

    if not all_mm_xy:
        msg = f"No closed sampled contours with enough detail in {svg_path}"
        raise ValueError(msg)

    min_x = min(xy[0] for xy in all_mm_xy)
    min_y = min(xy[1] for xy in all_mm_xy)
    max_x = max(xy[0] for xy in all_mm_xy)
    max_y = max(xy[1] for xy in all_mm_xy)
    bounds = Bounds(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)

    return SvgInput(
        path=svg_path,
        view_box=view_box,
        unit_scale_mm=unit_scale_mm,
        bounds=bounds,
        source_paths=tuple(source_paths),
    )


def parse_length_to_mm(value: str) -> float | None:
    """Parse an SVG length with a physical unit; return mm total or None if not applicable."""
    match = _LENGTH_RE.match(value.strip())
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "mm":
        return number
    if unit == "cm":
        return number * 10.0
    if unit == "in":
        return number * 25.4
    if unit == "pt":
        return number * 25.4 / 72.0
    if unit == "px":
        return number * 25.4 / 96.0
    return None


def derive_unit_scale_mm(
    root: ElementTree.Element,
    view_box: tuple[float, float, float, float],
) -> float:
    """Millimeters per SVG user unit (multiply a coordinate delta by this to get mm)."""
    _, _, vb_w, vb_h = view_box

    width_str = root.attrib.get("width")
    height_str = root.attrib.get("height")

    scale_from_width: float | None = None
    if width_str and vb_w > 0:
        physical_mm = parse_length_to_mm(width_str)
        if physical_mm is not None:
            scale_from_width = physical_mm / vb_w

    scale_from_height: float | None = None
    if height_str and vb_h > 0:
        physical_mm = parse_length_to_mm(height_str)
        if physical_mm is not None:
            scale_from_height = physical_mm / vb_h

    # When both width and height yield a scale, prefer width if they disagree.
    if scale_from_width is not None:
        return scale_from_width
    if scale_from_height is not None:
        return scale_from_height
    return 1.0


def _view_box_from_root(root: ElementTree.Element) -> tuple[float, float, float, float]:
    raw = root.attrib.get("viewBox")
    if raw:
        values = [float(v) for v in re.split(r"[,\s]+", raw.strip()) if v]
        if len(values) == 4:
            return values[0], values[1], values[2], values[3]
    return 0.0, 0.0, 1000.0, 1000.0
