"""Project name validation and layout paths under projects/<name>/."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lettersign.errors import InvalidProjectNameError


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved filesystem layout for a lettersign project (no I/O)."""

    root: Path
    project_dir: Path
    input_svg: Path
    config_toml: Path
    centerline_svg: Path
    data_scad: Path
    wrapper_scad: Path


def validate_project_name(name: str) -> str:
    """Return `name` if it is a safe single path component.

    Rules: non-empty, no leading/trailing whitespace, no path separators,
    not "." or "..", no NUL, and not an absolute path when interpreted as a segment.
    """
    if not name:
        raise InvalidProjectNameError("Project name must not be empty.")
    if name != name.strip():
        raise InvalidProjectNameError("Project name must not have leading or trailing whitespace.")
    if "\x00" in name:
        raise InvalidProjectNameError("Project name must not contain NUL characters.")
    if "/" in name or "\\" in name:
        raise InvalidProjectNameError(
            "Project name must be a single path component (no slashes or backslashes)."
        )
    if name in {".", ".."}:
        raise InvalidProjectNameError(
            "Project name must not be '.' or '..' (forbidden path segments)."
        )
    # Treat any path that parses as absolute as invalid for a project token.
    if Path(name).is_absolute():
        raise InvalidProjectNameError("Project name must not be an absolute path.")

    return name


def resolve_project(project_name: str, *, projects_root: Path = Path("projects")) -> ProjectPaths:
    """Map a project name to expected paths under `projects_root/<name>/` (no I/O)."""
    safe_name = validate_project_name(project_name)
    root = projects_root
    project_dir = root / safe_name
    return ProjectPaths(
        root=root,
        project_dir=project_dir,
        input_svg=project_dir / f"{safe_name}.svg",
        config_toml=project_dir / f"{safe_name}.toml",
        centerline_svg=project_dir / f"{safe_name}.centerline.svg",
        data_scad=project_dir / f"{safe_name}_data.scad",
        wrapper_scad=project_dir / f"{safe_name}.scad",
    )
