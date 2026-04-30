"""Tests for packaged OpenSCAD assets."""

from __future__ import annotations

import importlib.resources

from lettersign.scad_assets import common_scad_text


def test_common_scad_text_includes_post_module() -> None:
    assert "module lettersign_post" in common_scad_text()


def test_canonical_common_scad_readable_via_package_resources_api() -> None:
    """Bundled helper is loadable via `importlib.resources` (package-data path)."""
    ref = importlib.resources.files("lettersign.scad").joinpath("lettersign_common.scad")
    via_resources = ref.read_text(encoding="utf-8")
    assert via_resources == common_scad_text()
    assert len(via_resources) > 50
