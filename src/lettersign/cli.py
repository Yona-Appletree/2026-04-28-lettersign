"""Project-oriented CLI: init, build, watch, and legacy SVG entry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lettersign.centerline import main as centerline_main
from lettersign.config import load_or_create_config
from lettersign.errors import LettersignError, MissingInputSvgError
from lettersign.pipeline import build_centerline_preview
from lettersign.project import resolve_project


def split_projects_root(argv: list[str]) -> tuple[Path, list[str]]:
    """Strip a leading `--projects-root` / `-p` prefix; return (root, remaining argv)."""
    root = Path("projects")
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--projects-root", "-p"):
            if i + 1 >= len(argv):
                raise LettersignError(f"Missing value for `{a}` (expected a directory path).")
            root = Path(argv[i + 1])
            i += 2
        elif a.startswith("--projects-root="):
            root = Path(a.split("=", 1)[1].strip())
            i += 1
        else:
            return root, argv[i:]
    return root, []


def is_project_subcommand_argv(rest: list[str]) -> bool:
    return bool(rest) and rest[0] in {"init", "build", "watch"}


def should_delegate_legacy(rest: list[str]) -> bool:
    """Return true when argv looks like the old SVG-path centerline CLI."""
    return bool(rest) and rest[0] not in {"-h", "--help"} and not is_project_subcommand_argv(rest)


def delegate_centerline_legacy(rest: list[str]) -> None:
    """Run the legacy centerline CLI using `rest` as its argv tail (after program name)."""
    old = sys.argv
    try:
        prog = old[0] if old else "lettersign"
        sys.argv = [prog, *rest]
        centerline_main()
    finally:
        sys.argv = old


def cmd_init(project_name: str, projects_root: Path) -> None:
    paths = resolve_project(project_name, projects_root=projects_root)
    paths.project_dir.mkdir(parents=True, exist_ok=True)
    load_or_create_config(paths.config_toml)
    print(f"Initialized project {project_name!r} at {paths.project_dir}.")
    if not paths.input_svg.is_file():
        print(
            f"Next: add the input SVG at {paths.input_svg} (expected: {paths.input_svg.name}).",
            file=sys.stderr,
        )


def cmd_build(project_name: str, projects_root: Path) -> None:
    paths = resolve_project(project_name, projects_root=projects_root)
    paths.project_dir.mkdir(parents=True, exist_ok=True)
    config = load_or_create_config(paths.config_toml)
    if not paths.input_svg.is_file():
        raise MissingInputSvgError(
            f"Missing input SVG for project {project_name!r}: expected {paths.input_svg}. "
            "Run `lettersign init` or create that file, then try again."
        )
    out_path = build_centerline_preview(paths, config)
    print(f"Wrote centerline preview to {out_path}")


def cmd_watch(project_name: str, projects_root: Path) -> None:
    paths = resolve_project(project_name, projects_root=projects_root)
    load_or_create_config(paths.config_toml)
    print(
        "Watch mode (automatic rebuild on file changes) is planned for milestone 4 (M4). "
        f"Project {project_name!r} and config at {paths.config_toml} are ready."
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lettersign",
        description="Lettersign: project-oriented sign tooling (init / build / watch).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create project directory and TOML config.")
    p_init.add_argument("name", metavar="NAME", help="Project name (single path segment).")

    sub.add_parser("build", help="Refresh config and generate the centerline SVG.").add_argument(
        "name",
        metavar="NAME",
        help="Project name (single path segment).",
    )

    p_watch = sub.add_parser(
        "watch",
        help="Validate project layout (watch loop arrives in M4).",
    )
    p_watch.add_argument(
        "name",
        metavar="NAME",
        help="Project name (single path segment).",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)

    try:
        projects_root, rest = split_projects_root(argv)
    except LettersignError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(1) from e

    if should_delegate_legacy(rest):
        delegate_centerline_legacy(rest)
        return

    parser = build_arg_parser()
    args = parser.parse_args(rest)

    try:
        if args.command == "init":
            cmd_init(args.name, projects_root)
        elif args.command == "build":
            cmd_build(args.name, projects_root)
        elif args.command == "watch":
            cmd_watch(args.name, projects_root)
        else:  # pragma: no cover - argparse enforces choices
            parser.print_help(file=sys.stderr)
            raise SystemExit(2)
    except LettersignError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(1) from e
