"""Tests for project build pipeline orchestration."""

from __future__ import annotations

import textwrap
from pathlib import Path
from xml.etree import ElementTree

from lettersign.config import load_or_create_config
from lettersign.pipeline import build_centerline_preview
from lettersign.project import resolve_project

MINIMAL_CLOSED_SVG = textwrap.dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <path d="M 10 10 L 90 10 L 90 90 L 10 90 Z" fill="#000"/>
    </svg>
    """
)


def _svg_elements(root: ElementTree.Element, local_name: str) -> list[ElementTree.Element]:
    suffix = f"}}{local_name}"
    return [el for el in root.iter() if el.tag == local_name or el.tag.endswith(suffix)]


def test_build_centerline_preview_writes_normalized_svg(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    name = "demo"
    paths = resolve_project(name, projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.input_svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\n",
        encoding="utf-8",
    )
    config = load_or_create_config(paths.config_toml)

    out = build_centerline_preview(paths, config)

    assert out == paths.centerline_svg
    assert out.is_file()
    text = out.read_text(encoding="utf-8")

    cfg_root = ElementTree.fromstring(text)
    assert cfg_root.tag.endswith("svg")

    paths_el = _svg_elements(cfg_root, "path")
    assert len(paths_el) == 2
    outline_path, centerline_path = paths_el
    assert outline_path.get("fill") == "none"
    assert outline_path.get("stroke") in ("#000000", "black")
    assert centerline_path.get("fill") == "none"
    assert centerline_path.get("stroke") in ("#ff0000", "red")
    assert float(centerline_path.get("stroke-width", "0")) == config.led_channel_width

    circles = _svg_elements(cfg_root, "circle")
    assert len(circles) >= 1
    for circle in circles:
        assert circle.get("fill") == "#008000"
        assert circle.get("stroke") == "#008000"


def test_build_centerline_preview_uses_led_channel_width_from_config(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    name = "wide"
    paths = resolve_project(name, projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.input_svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\nled_channel_width = 7.5\n",
        encoding="utf-8",
    )
    config = load_or_create_config(paths.config_toml)
    assert config.led_channel_width == 7.5

    build_centerline_preview(paths, config)

    text = paths.centerline_svg.read_text(encoding="utf-8")
    cfg_root = ElementTree.fromstring(text)
    paths_el = _svg_elements(cfg_root, "path")
    _, centerline_path = paths_el
    assert float(centerline_path.get("stroke-width", "0")) == 7.5
