"""Tests for ProjectConfig load/create and comment-preserving TOML merge."""

from __future__ import annotations

from pathlib import Path

import pytest

from lettersign.config import DEFAULTS, ProjectConfig, load_or_create_config
from lettersign.errors import InvalidConfigError, LettersignError


def test_load_or_create_writes_defaults_when_missing(tmp_path: Path) -> None:
    path = tmp_path / "demo" / "demo.toml"
    assert not path.exists()

    cfg = load_or_create_config(path)

    assert cfg == ProjectConfig()
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Lettersign project configuration" in text
    for key in DEFAULTS:
        assert f"{key} =" in text


def test_existing_config_preserves_user_values(tmp_path: Path) -> None:
    path = tmp_path / "demo.toml"
    path.write_text(
        "# custom\nheight = 22.5\nled_channel_width = 3.0\n"
        "post_height = 11.0\nline_resolution = 0.125\n",
        encoding="utf-8",
    )

    cfg = load_or_create_config(path)

    assert cfg.height == 22.5
    assert cfg.led_channel_width == 3.0
    assert cfg.post_height == 11.0
    assert cfg.line_resolution == 0.125


def test_missing_keys_are_appended_with_defaults(tmp_path: Path) -> None:
    path = tmp_path / "demo.toml"
    path.write_text("# header\nheight = 40.0\n", encoding="utf-8")

    cfg = load_or_create_config(path)

    assert cfg.height == 40.0
    assert cfg.led_channel_width == DEFAULTS["led_channel_width"]
    assert cfg.post_height == DEFAULTS["post_height"]
    assert cfg.line_resolution == DEFAULTS["line_resolution"]

    updated = path.read_text(encoding="utf-8")
    assert "# header" in updated
    assert "led_channel_width" in updated
    assert "line_resolution =" in updated


def test_comments_survive_update_when_missing_key_added(tmp_path: Path) -> None:
    """Practical preservation: merging should not drop prior comment lines."""
    path = tmp_path / "demo.toml"
    path.write_text(
        "# Tune these for LED strip clearance\nheight = 16.2\npost_height = 12.7\n\n",
        encoding="utf-8",
    )

    load_or_create_config(path)

    text = path.read_text(encoding="utf-8")
    assert "# Tune these for LED strip clearance" in text
    assert "height = 16.2" in text
    assert "post_height = 12.7" in text


def _bad_path(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "bad.toml"
    p.write_text(body, encoding="utf-8")
    return p


def test_invalid_height_string_raises_errors(tmp_path: Path) -> None:
    path = _bad_path(tmp_path, 'height = "oops"\n')
    with pytest.raises(InvalidConfigError) as excinfo:
        load_or_create_config(path)
    err = excinfo.value
    assert isinstance(err, LettersignError)
    assert path.name in str(err)


def test_invalid_height_bool_raises_errors(tmp_path: Path) -> None:
    path = _bad_path(tmp_path, "height = true\n")
    with pytest.raises(InvalidConfigError, match=r"boolean"):
        load_or_create_config(path)


def test_invalid_scalar_type_raises_errors(tmp_path: Path) -> None:
    path = _bad_path(tmp_path, "height = []\n")
    with pytest.raises(InvalidConfigError, match=r"scalar"):
        load_or_create_config(path)


def test_negative_value_raises_errors(tmp_path: Path) -> None:
    body = """height = 15.0
led_channel_width = 3.0
post_height = -1.0
line_resolution = 0.25
"""
    path = _bad_path(tmp_path, body)
    with pytest.raises(InvalidConfigError) as excinfo:
        load_or_create_config(path)
    assert "post_height" in str(excinfo.value)
