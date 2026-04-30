"""Tests for project name validation and path layout."""

from __future__ import annotations

from pathlib import Path

import pytest

from lettersign.errors import InvalidProjectNameError
from lettersign.project import ProjectPaths, resolve_project, validate_project_name


@pytest.mark.parametrize(
    "name",
    [
        "demo",
        "my-sign",
        "sign01",
        "letters_a",
        "A",
    ],
)
def test_validate_project_name_accepts_safe_names(name: str) -> None:
    assert validate_project_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        "  \t ",
        " foo",
        "foo ",
        "foo/bar",
        "foo\\bar",
        ".",
        "..",
        "foo\x00bar",
    ],
)
def test_validate_project_name_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(InvalidProjectNameError):
        validate_project_name(name)


def test_validate_project_name_rejects_when_path_reports_absolute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Platform-specific absolute paths are covered by separator checks; this pins the fallback."""

    monkeypatch.setattr(Path, "is_absolute", lambda self: True)
    with pytest.raises(InvalidProjectNameError, match="absolute path"):
        validate_project_name("looks_relative")


def test_resolve_project_paths_layout(tmp_path: Path) -> None:
    root = tmp_path / "myprojects"
    p = resolve_project("demo", projects_root=root)
    assert p == ProjectPaths(
        root=root,
        project_dir=root / "demo",
        input_svg=root / "demo" / "demo.svg",
        config_toml=root / "demo" / "demo.toml",
        centerline_svg=root / "demo" / "demo.centerline.svg",
        data_scad=root / "demo" / "demo_data.scad",
        wrapper_scad=root / "demo" / "demo.scad",
        common_scad=root / "lettersign_common.scad",
    )


def test_resolve_project_common_scad_at_projects_root(tmp_path: Path) -> None:
    root = tmp_path / "myprojects"
    expected = root / "lettersign_common.scad"
    assert resolve_project("demo", projects_root=root).common_scad == expected


def test_resolve_project_validates_name(tmp_path: Path) -> None:
    with pytest.raises(InvalidProjectNameError):
        resolve_project("../escape", projects_root=tmp_path)


def test_resolve_project_default_root_is_projects_relative() -> None:
    p = resolve_project("x")
    assert p.root == Path("projects")
    assert p.project_dir == Path("projects") / "x"
