"""Tests for watch internals and timeout-bounded watch smoke paths."""

from __future__ import annotations

import io
import textwrap
import threading
import time
from pathlib import Path

import pytest

from lettersign.config import load_or_create_config
from lettersign.errors import LettersignError
from lettersign.project import resolve_project
from lettersign.watcher import (
    WatchSettings,
    snapshot_watched_inputs,
    watch_project,
    watched_input_paths,
)

MINIMAL_CLOSED_SVG = textwrap.dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <path d="M 10 10 L 90 10 L 90 90 L 10 90 Z" fill="#000"/>
    </svg>
    """
)


def test_watched_input_paths_are_only_svg_and_toml(tmp_path: Path) -> None:
    paths = resolve_project("demo", projects_root=tmp_path)
    assert watched_input_paths(paths) == (paths.input_svg, paths.config_toml)


def test_snapshot_watched_inputs_none_for_missing_files(tmp_path: Path) -> None:
    paths = resolve_project("demo", projects_root=tmp_path)
    paths.project_dir.mkdir(parents=True)
    snap = snapshot_watched_inputs(paths)
    assert snap[paths.input_svg] is None
    assert snap[paths.config_toml] is None

    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\n",
        encoding="utf-8",
    )
    snap2 = snapshot_watched_inputs(paths)
    assert snap2[paths.input_svg] is None
    assert snap2[paths.config_toml] is not None


def test_watch_once_performs_one_build_and_writes_outputs(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    name = "demo"
    paths = resolve_project(name, projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.input_svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\n",
        encoding="utf-8",
    )
    load_or_create_config(paths.config_toml)

    out = io.StringIO()
    watch_project(paths, settings=WatchSettings(once=True), stdout=out)

    assert paths.centerline_svg.is_file()
    assert paths.data_scad.is_file()
    assert paths.wrapper_scad.is_file()
    assert paths.common_scad.is_file()
    assert "Wrote centerline preview" in out.getvalue()


def test_watch_preserves_custom_wrapper_after_triggered_rebuild(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    name = "demo"
    paths = resolve_project(name, projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.input_svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\nheight = 10.0\n",
        encoding="utf-8",
    )
    load_or_create_config(paths.config_toml)

    watch_project(paths, settings=WatchSettings(once=True))

    sentinel = "// watch wrapper sentinel\nuse <custom.scad>\n\n"
    paths.wrapper_scad.write_text(sentinel, encoding="utf-8")
    first_data = paths.data_scad.read_text(encoding="utf-8")

    change_done = threading.Event()

    def bump_toml() -> None:
        time.sleep(0.08)
        paths.config_toml.write_text(
            "# Lettersign project configuration (lengths in millimeters).\n\nheight = 22.0\n",
            encoding="utf-8",
        )
        change_done.set()

    threading.Thread(target=bump_toml, daemon=True).start()

    watch_project(
        paths,
        settings=WatchSettings(interval_seconds=0.01, debounce_seconds=0.01),
        stop_after_rebuilds=2,
    )

    assert change_done.wait(timeout=5.0)
    assert paths.wrapper_scad.read_text(encoding="utf-8") == sentinel
    second_data = paths.data_scad.read_text(encoding="utf-8")
    assert "demo_height = 22" in second_data
    assert second_data != first_data


def test_watch_detects_toml_change_under_timeout(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    name = "demo"
    paths = resolve_project(name, projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.input_svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\nled_channel_width = 3.0\n",
        encoding="utf-8",
    )
    load_or_create_config(paths.config_toml)

    watch_project(paths, settings=WatchSettings(once=True))
    first_data = paths.data_scad.read_text(encoding="utf-8")

    change_done = threading.Event()

    def widen_channel() -> None:
        time.sleep(0.08)
        paths.config_toml.write_text(
            "# Lettersign project configuration (lengths in millimeters).\n\n"
            "led_channel_width = 9.25\n",
            encoding="utf-8",
        )
        change_done.set()

    threading.Thread(target=widen_channel, daemon=True).start()

    watch_project(
        paths,
        settings=WatchSettings(interval_seconds=0.01, debounce_seconds=0.01),
        stop_after_rebuilds=2,
    )

    assert change_done.wait(timeout=5.0)
    second_data = paths.data_scad.read_text(encoding="utf-8")
    assert "demo_led_channel_width = 9.25" in second_data
    assert second_data != first_data


def test_watch_prints_error_on_failed_rebuild_then_recovers(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    name = "demo"
    paths = resolve_project(name, projects_root=root)
    paths.project_dir.mkdir(parents=True)
    paths.input_svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    paths.config_toml.write_text(
        "# Lettersign project configuration (lengths in millimeters).\n\n",
        encoding="utf-8",
    )
    load_or_create_config(paths.config_toml)

    good_svg = MINIMAL_CLOSED_SVG
    stderr = io.StringIO()
    steps_done = threading.Event()

    def corrupt_then_fix() -> None:
        time.sleep(0.06)
        paths.input_svg.write_text("<svg>not valid geometry</svg>", encoding="utf-8")
        time.sleep(0.08)
        paths.input_svg.write_text(good_svg, encoding="utf-8")
        steps_done.set()

    threading.Thread(target=corrupt_then_fix, daemon=True).start()

    watch_project(
        paths,
        settings=WatchSettings(interval_seconds=0.01, debounce_seconds=0.01),
        stderr=stderr,
        stop_after_rebuilds=2,
    )

    assert steps_done.wait(timeout=5.0)
    err = stderr.getvalue()
    assert err.strip() != ""
    assert paths.centerline_svg.is_file()


def test_validate_watch_settings_rejects_bad_interval() -> None:
    paths = resolve_project("demo", projects_root=Path("/nonexistent"))
    with pytest.raises(LettersignError) as exc:
        watch_project(paths, settings=WatchSettings(interval_seconds=0.0, once=True))
    assert "interval" in str(exc.value).lower()


def test_validate_watch_settings_rejects_negative_debounce() -> None:
    paths = resolve_project("demo", projects_root=Path("/nonexistent"))
    with pytest.raises(LettersignError) as exc:
        watch_project(paths, settings=WatchSettings(debounce_seconds=-0.1, once=True))
    assert "debounce" in str(exc.value).lower()
