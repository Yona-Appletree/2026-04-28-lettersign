"""Stdlib polling watch loop for project input SVG and TOML."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from lettersign.config import load_or_create_config
from lettersign.errors import LettersignError, MissingInputSvgError
from lettersign.pipeline import build_centerline_preview
from lettersign.project import ProjectPaths


@dataclass(frozen=True)
class WatchSettings:
    interval_seconds: float = 0.5
    debounce_seconds: float = 0.2
    once: bool = False


def watched_input_paths(paths: ProjectPaths) -> tuple[Path, Path]:
    return paths.input_svg, paths.config_toml


def snapshot_watched_inputs(paths: ProjectPaths) -> dict[Path, int | None]:
    out: dict[Path, int | None] = {}
    for path in watched_input_paths(paths):
        out[path] = path.stat().st_mtime_ns if path.is_file() else None
    return out


def watch_project(
    paths: ProjectPaths,
    *,
    settings: WatchSettings | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    stop_after_rebuilds: int | None = None,
) -> None:
    resolved = WatchSettings() if settings is None else settings
    _validate_watch_settings(resolved)

    rebuild_count = 0

    def try_build() -> None:
        nonlocal rebuild_count
        config = load_or_create_config(paths.config_toml)
        if not paths.input_svg.is_file():
            raise MissingInputSvgError(
                f"Missing input SVG for project {paths.project_dir.name!r}: "
                f"expected {paths.input_svg}. "
                "Run `lettersign init` or create that file, then try again."
            )
        out_path = build_centerline_preview(paths, config)
        rebuild_count += 1
        print(f"Wrote centerline preview to {out_path}", file=stdout)

    try_build()

    if resolved.once:
        return
    if stop_after_rebuilds is not None and rebuild_count >= stop_after_rebuilds:
        return

    snap = snapshot_watched_inputs(paths)
    while True:
        time.sleep(resolved.interval_seconds)
        if snapshot_watched_inputs(paths) == snap:
            continue
        time.sleep(resolved.debounce_seconds)
        try:
            try_build()
            snap = snapshot_watched_inputs(paths)
            if stop_after_rebuilds is not None and rebuild_count >= stop_after_rebuilds:
                return
        except LettersignError as e:
            print(str(e), file=stderr)
            snap = snapshot_watched_inputs(paths)


def _validate_watch_settings(settings: WatchSettings) -> None:
    if settings.interval_seconds <= 0:
        raise LettersignError(
            f"Watch --interval must be positive, got {settings.interval_seconds}."
        )
    if settings.debounce_seconds < 0:
        raise LettersignError(
            f"Watch --debounce must be non-negative, got {settings.debounce_seconds}."
        )
