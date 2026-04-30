"""Structural tests for OpenSCAD data and wrapper rendering."""

from __future__ import annotations

from pathlib import Path

from lettersign.config import PREVIEW_MARKER_RADIUS_MM
from lettersign.geometry import Point
from lettersign.project import resolve_project
from lettersign.render_scad import (
    GENERATED_DATA_SCAD_COMMENT,
    render_data_scad,
    render_wrapper_scad,
    write_scad_outputs,
)
from lettersign.scad_geometry import (
    ScadModel,
    ScadPathPart,
    ScadPolygon,
    ScadPost,
)


def _demo_model() -> ScadModel:
    outline = ScadPolygon(
        points=(
            Point(0.0, 0.0),
            Point(100.0, 0.0),
            Point(100.0, 100.0),
            Point(0.0, 100.0),
        ),
        paths=((0, 1, 2, 3),),
    )
    channel = ScadPolygon(
        points=(
            Point(40.0, 40.0),
            Point(60.0, 40.0),
            Point(60.0, 60.0),
            Point(40.0, 60.0),
        ),
        paths=((0, 1, 2, 3),),
    )
    posts = (
        ScadPost(
            position=Point(50.0, 50.0),
            radius_mm=PREVIEW_MARKER_RADIUS_MM,
            height_mm=42.375,
        ),
    )
    part = ScadPathPart(name="path1", outline=outline, channels=(channel,), posts=posts)
    return ScadModel(
        project_name="demo",
        height_mm=18.875,
        led_channel_width_mm=3.0625,
        post_height_mm=42.375,
        parts=(part,),
    )


def test_render_data_scad_structure() -> None:
    model = _demo_model()
    body = render_data_scad(model)
    assert body.splitlines()[0] == f"// {GENERATED_DATA_SCAD_COMMENT}"
    assert GENERATED_DATA_SCAD_COMMENT in body
    assert "use <../lettersign_common.scad>" in body
    assert "module path1_outline()" in body
    assert "module path1_channel()" in body
    assert "module path1_posts()" in body
    assert "module path1_3d()" in body
    assert "module demo_3d()" in body
    assert "polygon(points=" in body
    assert "lettersign_post(" in body
    assert "demo_height = 18.875" in body
    assert "demo_led_channel_width = 3.0625" in body
    assert "demo_post_height = 42.375" in body
    assert "linear_extrude(height=demo_height + 0.2)" in body


def test_render_wrapper_scad_structure() -> None:
    txt = render_wrapper_scad("demo")
    lines = txt.splitlines()
    assert lines[0].startswith("// ")
    assert "use <demo_data.scad>" in txt
    assert "demo_3d();" in txt


def test_write_scad_outputs_preserves_existing_wrapper(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    paths = resolve_project("demo", projects_root=root)
    paths.project_dir.mkdir(parents=True)
    sentinel = "// user customized wrapper --- do not revert\nuse <other.scad>\n\n"
    paths.wrapper_scad.write_text(sentinel, encoding="utf-8")
    write_scad_outputs(paths, _demo_model())

    assert paths.wrapper_scad.read_text(encoding="utf-8") == sentinel
    data = paths.data_scad.read_text(encoding="utf-8")
    assert "module demo_3d()" in data
    assert paths.common_scad.exists()
    assert "module lettersign_post" in paths.common_scad.read_text(encoding="utf-8")


def test_write_scad_outputs_overwrites_stale_data_scad(tmp_path: Path) -> None:
    """Generated data SCAD must be refreshed even when stale content exists."""
    root = tmp_path / "projects"
    paths = resolve_project("demo", projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.common_scad.parent.mkdir(parents=True, exist_ok=True)
    stale = "// STALE demo_data - tool must replace this\nmodule stale() {}\n"
    paths.data_scad.write_text(stale, encoding="utf-8")

    write_scad_outputs(paths, _demo_model())

    data = paths.data_scad.read_text(encoding="utf-8")
    assert "STALE demo_data" not in data
    assert f"// {GENERATED_DATA_SCAD_COMMENT}" in data
    assert "module demo_3d()" in data


def test_write_scad_outputs_overwrites_stale_common_scad(tmp_path: Path) -> None:
    """Shared helper must be regenerated when outdated content sits on disk."""
    root = tmp_path / "projects"
    paths = resolve_project("demo", projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.common_scad.parent.mkdir(parents=True, exist_ok=True)
    paths.common_scad.write_text("// STALE lettersign_common - regenerate me\n", encoding="utf-8")

    write_scad_outputs(paths, _demo_model())

    common = paths.common_scad.read_text(encoding="utf-8")
    assert "STALE lettersign_common" not in common
    assert "module lettersign_post" in common


def test_write_scad_outputs_does_not_overwrite_wrapper_with_custom_text(tmp_path: Path) -> None:
    existing = "// custom user wrapper body\nuse <manual.scad>\n\ncustom_module();\n"
    root = tmp_path / "projects"
    paths = resolve_project("demo", projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.wrapper_scad.write_text(existing, encoding="utf-8")
    write_scad_outputs(paths, _demo_model())
    assert paths.wrapper_scad.read_text(encoding="utf-8") == existing


def test_write_scad_outputs_creates_wrapper_with_data_use_and_3d_call(tmp_path: Path) -> None:
    """New wrapper references data SCAD via `use` and calls the prefixed `_3d` module."""
    root = tmp_path / "projects"
    paths = resolve_project("demo", projects_root=root)
    paths.project_dir.mkdir(parents=True)
    assert not paths.wrapper_scad.exists()

    write_scad_outputs(paths, _demo_model())

    wrapper = paths.wrapper_scad.read_text(encoding="utf-8")
    assert "use <demo_data.scad>" in wrapper
    assert "demo_3d();" in wrapper
