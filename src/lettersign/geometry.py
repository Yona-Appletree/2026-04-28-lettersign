"""Typed domain geometry for the lettersign pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float


@dataclass(frozen=True)
class SourcePath:
    name: str
    rings: tuple[tuple[Point, ...], ...]


@dataclass(frozen=True)
class SvgInput:
    path: Path
    view_box: tuple[float, float, float, float]
    unit_scale_mm: float
    bounds: Bounds
    source_paths: tuple[SourcePath, ...]


@dataclass(frozen=True)
class Marker:
    """A detected post / preview marker in millimeter space."""

    position: Point
    radius_mm: float
    kind: str | None = None
