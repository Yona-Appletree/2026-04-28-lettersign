"""Access to OpenSCAD sources shipped inside the lettersign package."""

from __future__ import annotations

import importlib.resources


def common_scad_text() -> str:
    """Return the canonical `lettersign_common.scad` source bundled with the package."""
    path = importlib.resources.files("lettersign.scad").joinpath("lettersign_common.scad")
    return path.read_text(encoding="utf-8")
