"""Tests for project build pipeline orchestration."""

from __future__ import annotations

import textwrap
from pathlib import Path
from xml.etree import ElementTree

from lettersign.config import load_or_create_config
from lettersign.pipeline import build_centerline_preview
from lettersign.project import resolve_project
from lettersign.render_scad import GENERATED_DATA_SCAD_COMMENT

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


def test_build_centerline_preview_writes_scad_outputs(tmp_path: Path) -> None:
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

    build_centerline_preview(paths, config)

    assert paths.data_scad.is_file()
    assert paths.wrapper_scad.is_file()
    assert paths.common_scad.is_file()

    data = paths.data_scad.read_text(encoding="utf-8")
    assert data.splitlines()[0] == f"// {GENERATED_DATA_SCAD_COMMENT}"
    assert "use <../lettersign_common.scad>" in data
    for mod in (
        "module path1_outline()",
        "module path1_channel()",
        "module path1_posts()",
        "module path1_3d()",
    ):
        assert mod in data

    wrapper = paths.wrapper_scad.read_text(encoding="utf-8")
    assert "use <demo_data.scad>" in wrapper
    assert "demo_3d();" in wrapper


def test_build_centerline_preview_preserves_wrapper_on_rebuild(tmp_path: Path) -> None:
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

    build_centerline_preview(paths, config)
    sentinel = "// user customized wrapper --- keep on rebuild\nuse <other.scad>\n\n"
    paths.wrapper_scad.write_text(sentinel, encoding="utf-8")

    build_centerline_preview(paths, config)

    assert paths.wrapper_scad.read_text(encoding="utf-8") == sentinel
    assert "module path1_outline()" in paths.data_scad.read_text(encoding="utf-8")


def test_build_twice_refreshes_data_scad_while_preserving_custom_wrapper(tmp_path: Path) -> None:
    """Second build refreshes generated data SCAD without touching a user-edited wrapper."""
    root = tmp_path / "projects"
    name = "demo"
    paths = resolve_project(name, projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.input_svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\nheight = 12.0\n",
        encoding="utf-8",
    )
    config = load_or_create_config(paths.config_toml)
    build_centerline_preview(paths, config)

    first_data = paths.data_scad.read_text(encoding="utf-8")

    sentinel = "// two-build sentinel - must survive second build\nuse <other.scad>\n\n"
    paths.wrapper_scad.write_text(sentinel, encoding="utf-8")

    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\nheight = 24.5\n",
        encoding="utf-8",
    )
    config_second = load_or_create_config(paths.config_toml)
    build_centerline_preview(paths, config_second)

    assert paths.wrapper_scad.read_text(encoding="utf-8") == sentinel

    second_data = paths.data_scad.read_text(encoding="utf-8")
    assert "demo_height = 24.5" in second_data
    assert second_data != first_data
    assert f"// {GENERATED_DATA_SCAD_COMMENT}" in second_data


def test_build_writes_common_scad_at_projects_root_not_inside_project(tmp_path: Path) -> None:
    """Shared helper stays at `<projects_root>/lettersign_common.scad`, not under `<name>/`."""
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
    build_centerline_preview(paths, config)

    assert paths.common_scad.is_file()
    assert paths.common_scad.parent.resolve() == root.resolve()
    assert not paths.common_scad.resolve().is_relative_to(paths.project_dir.resolve())
