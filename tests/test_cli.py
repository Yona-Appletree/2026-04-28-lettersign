"""Tests for the lettersign project CLI (init / build / watch / legacy SVG)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from lettersign import cli

MINIMAL_CLOSED_SVG = textwrap.dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <path d="M 10 10 L 90 10 L 90 90 L 10 90 Z" fill="#000"/>
    </svg>
    """
)


def test_init_creates_layout_and_reports_svg(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli.main(["-p", str(tmp_path), "init", "demo"])

    proj = tmp_path / "demo"
    assert proj.is_dir()
    assert (proj / "demo.toml").is_file()

    captured = capsys.readouterr()
    assert "Initialized project" in captured.out
    assert "demo" in captured.out
    assert "demo.svg" in captured.err


def test_build_fails_when_svg_missing(tmp_path: Path) -> None:
    cli.main(["-p", str(tmp_path), "init", "demo"])

    with pytest.raises(SystemExit) as exc:
        cli.main(["-p", str(tmp_path), "build", "demo"])
    assert exc.value.code == 1


def test_build_writes_centerline_when_svg_present(tmp_path: Path) -> None:
    cli.main(["-p", str(tmp_path), "init", "demo"])
    svg = tmp_path / "demo" / "demo.svg"
    svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")

    cli.main(["-p", str(tmp_path), "build", "demo"])

    out_path = tmp_path / "demo" / "demo.centerline.svg"
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert "<svg" in text


def test_invalid_project_name_exits_nonzero(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["-p", str(tmp_path), "init", "foo/bar"])
    assert exc.value.code == 1


def test_watch_is_stub(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["-p", str(tmp_path), "watch", "demo"])

    out = capsys.readouterr().out
    assert "M4" in out
    assert "demo" in out


def test_top_level_help_shows_project_cli(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    assert "init" in capsys.readouterr().out


def test_legacy_invokes_centerline_for_svg_args(tmp_path: Path) -> None:
    svg = tmp_path / "demo.svg"
    svg.write_text(MINIMAL_CLOSED_SVG, encoding="utf-8")
    output = tmp_path / "demo.centerline.svg"

    cli.main([str(svg), "--preset", "fast", "-o", str(output)])

    assert output.is_file()


def test_missing_projects_root_flag_value() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["-p"])
    assert exc.value.code == 1

    with pytest.raises(SystemExit) as exc:
        cli.main(["--projects-root"])
    assert exc.value.code == 1
