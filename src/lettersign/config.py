"""Typed project configuration and TOML read/update/write (comment-preserving)."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import tomlkit
from tomlkit import TOMLDocument

from lettersign.errors import InvalidConfigError

# --- Preview / pipeline constants (not user TOML) ---------------------------

PREVIEW_MARKER_RADIUS_MM = 5.0

# --- Domain -----------------------------------------------------------------

CONFIG_KEY_ORDER = (
    "height",
    "led_channel_width",
    "post_height",
    "line_resolution",
)


@dataclass(frozen=True)
class ProjectConfig:
    """Lettersign tuning values persisted in `<name>.toml` (lengths in millimeters)."""

    height: float = 15.0
    led_channel_width: float = 3.0
    post_height: float = 12.0
    line_resolution: float = 0.25


def _defaults_map() -> dict[str, float]:
    d = ProjectConfig()
    return {
        "height": d.height,
        "led_channel_width": d.led_channel_width,
        "post_height": d.post_height,
        "line_resolution": d.line_resolution,
    }


DEFAULTS: dict[str, float] = _defaults_map()


# --- Public API -------------------------------------------------------------


def load_or_create_config(path: Path, *, encoding: str = "utf-8") -> ProjectConfig:
    """Load project config from `path`, creating the file with defaults if missing.

    Missing schema keys are inserted with defaults. The file is written only when
    it is created or when at least one key was appended. Invalid numeric entries
    raise `InvalidConfigError` with path and field context.
    """
    created = False
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = _new_default_document()
        created = True
    else:
        text = path.read_text(encoding=encoding)
        doc = _parse_document(text)

    appended = _append_missing_defaults(doc)

    values = _read_field_values(doc, path)

    cfg = ProjectConfig(
        height=values["height"],
        led_channel_width=values["led_channel_width"],
        post_height=values["post_height"],
        line_resolution=values["line_resolution"],
    )

    if created or appended:
        path.write_text(_render_document(doc), encoding=encoding, newline="\n")

    return cfg


# --- TOML document layer (tomlkit) ------------------------------------------


def _new_default_document() -> TOMLDocument:
    text = "# Lettersign project configuration (lengths in millimeters).\n\n"
    doc = _parse_document(text)
    _append_missing_defaults(doc)
    return doc


def _parse_document(src: str) -> TOMLDocument:
    return tomlkit.parse(src)


def _render_document(doc: TOMLDocument) -> str:
    return doc.as_string()


def _append_missing_defaults(doc: TOMLDocument) -> bool:
    changed = False
    for key in CONFIG_KEY_ORDER:
        if key not in doc:
            doc.append(key, DEFAULTS[key])
            changed = True
    return changed


def _read_field_values(doc: TOMLDocument, path: Path) -> Mapping[str, float]:
    out: dict[str, float] = {}
    for key in CONFIG_KEY_ORDER:
        raw = _take_required(doc, key, path)
        out[key] = _parse_positive_finite_float(str(key), raw, path)
    return out


def _take_required(doc: Mapping[str, object], key: str, path: Path) -> object:
    try:
        return doc[key]
    except KeyError as e:
        msg = (
            f"Missing required configuration key `{key}` in {path}. "
            "This should have been repaired automatically; repair the file or delete it "
            "and let lettersign recreate defaults."
        )
        raise InvalidConfigError(msg) from e


def _unwrap_toml_value(raw: object) -> object:
    unwrap = getattr(raw, "unwrap", None)
    if callable(unwrap):
        return raw.unwrap()  # type: ignore[no-any-return, union-attr]
    return raw


def _parse_positive_finite_float(field_name: str, raw: object, path: Path) -> float:
    val = _unwrap_toml_value(raw)

    if isinstance(val, bool):
        raise InvalidConfigError(
            _bad_msg(field_name, path, "expected a number, not a boolean."),
        )

    if isinstance(val, datetime):
        raise InvalidConfigError(
            _bad_msg(field_name, path, "expected a number, not a date/time."),
        )

    if isinstance(val, (list, dict)):
        raise InvalidConfigError(
            _bad_msg(field_name, path, "expected a scalar number (found table or array)."),
        )

    try:
        if isinstance(val, (int, float)):
            n = float(val)
        elif isinstance(val, str):
            n = float(val.strip())
        else:
            raise InvalidConfigError(
                _bad_msg(field_name, path, f"unsupported value type {type(val).__name__!r}."),
            )
    except ValueError as e:
        raise InvalidConfigError(
            _bad_msg(field_name, path, "could not parse as a finite number."),
        ) from e

    if math.isnan(n) or math.isinf(n):
        raise InvalidConfigError(
            _bad_msg(field_name, path, "value must be finite (not nan or inf)."),
        )

    if n <= 0:
        raise InvalidConfigError(
            f"Invalid `{field_name}` in {path}: value must be a positive finite number (got {n!r})."
        )

    return n


def _bad_msg(field_name: str, path: Path, detail: str) -> str:
    return f"Invalid `{field_name}` in {path}: {detail}"
