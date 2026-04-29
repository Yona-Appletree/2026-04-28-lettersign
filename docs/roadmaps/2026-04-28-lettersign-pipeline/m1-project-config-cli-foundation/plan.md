# Milestone 1 Plan: Project/config/CLI foundation

## Goal

Move `lettersign` from a raw SVG command toward a project-oriented CLI by adding
project path resolution, schema-managed TOML config, and explicit
`init`/`build`/`watch` command shape. This milestone should keep the current
centerline behavior working while creating clean seams for later pipeline and
SCAD milestones.

## Current state

- `pyproject.toml` exposes `lettersign = "lettersign.centerline:main"`.
- `src/lettersign/centerline.py` owns both CLI parsing and centerline
  generation.
- There are no `project.py`, `config.py`, `cli.py`, or user-facing error types.
- `tests/test_lettersign.py` is only a package-version smoke test.
- `README.md` currently documents the old SVG-path CLI and the planned project
  workflow.

## Design decisions

- Add a new `lettersign.cli:main` entrypoint and repoint the console script to
  it.
- Preserve current SVG-path behavior via an explicit legacy/compatibility path
  during this milestone. Later milestones can remove or narrow it after
  `build` owns the full pipeline.
- Use `tomlkit` for config read/update/write so user comments and existing
  values survive schema updates.
- Keep `ProjectConfig` as a typed domain object. The TOML document/update layer
  converts to/from that object instead of leaking `tomlkit` details through the
  pipeline.
- Treat `watch` as command-shape only for M1: it should validate project/config
  resolution and report that real watch behavior lands in M4, not spin a watch
  loop yet.

## Implementation phases

### Phase 1: Project paths and user-facing errors

Add `src/lettersign/errors.py` with a small `LettersignError` hierarchy or a
single domain exception plus CLI formatting helper.

Add `src/lettersign/project.py`:

- `ProjectName` validation or a function that validates project names are simple
  path components.
- `ProjectPaths` dataclass with:
  - `root`,
  - `project_dir`,
  - `input_svg`,
  - `config_toml`,
  - `centerline_svg`,
  - `data_scad`,
  - `wrapper_scad`.
- `resolve_project(project_name: str, *, projects_root: Path = Path("projects"))`.
- Tests for valid names, invalid names, and expected path layout.

Use `Path` values throughout and avoid filesystem side effects in pure path
resolution.

### Phase 2: Typed config and TOML update layer

Add `tomlkit` to project dependencies.

Add `src/lettersign/config.py`:

- `ProjectConfig` dataclass with defaults:
  - `height: float = 15.0`,
  - `led_channel_width: float = 3.0`,
  - `post_height: float = 12.0`,
  - `line_resolution: float = 0.25`.
- `load_or_create_config(path: Path) -> ProjectConfig` or a pair of functions
  that make filesystem behavior explicit.
- TOML update behavior:
  - create a missing TOML file with defaults and brief comments,
  - preserve existing values,
  - add missing keys when the schema has grown,
  - reject invalid numeric values with actionable errors.

Tests:

- missing config creates defaults,
- existing config preserves user values,
- missing new keys are appended,
- invalid values raise `LettersignError`,
- comments survive an update where practical.

### Phase 3: CLI command surface

Add `src/lettersign/cli.py` using `argparse`:

- `lettersign init <name>`
  - create `projects/<name>/` if needed,
  - create/update `<name>.toml`,
  - create `<name>.scad` wrapper only if absent, or leave wrapper creation to M3
    if it would be misleading before SCAD generation exists,
  - report expected input SVG path if missing.
- `lettersign build <name>`
  - resolve paths,
  - create/update config,
  - require `<name>.svg`,
  - for M1, call the existing centerline generation with project input/output
    paths if straightforward; otherwise provide a clear "pipeline arrives in
    M2" error and keep the old SVG command reachable.
- `lettersign watch <name>`
  - resolve paths and config,
  - report that watch mode is planned for M4.
- Optional compatibility:
  - if invoked like the old CLI with a path ending in `.svg`, delegate to
    `lettersign.centerline.main` or a renamed compatibility function.

Keep CLI return behavior testable: parse errors and domain errors should become
non-zero exits with useful messages.

Tests:

- command parser/CLI tests for `init`, `build` missing SVG, invalid project
  names, and compatibility path if retained.
- Use `tmp_path` so tests do not touch real `projects/`.

### Phase 4: Wire packaging and docs

Update `pyproject.toml`:

- add `tomlkit`,
- set `lettersign = "lettersign.cli:main"`.

Update `README.md` so the implemented behavior is accurate:

- show `init`, `build`, and `watch` status,
- describe config defaults,
- note any temporary compatibility command for raw SVG input.

Run:

```bash
uv lock
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

(See **Notes** below: `tomlkit` was added in Phase 2; Phase 4 repoints the console script and refreshes docs.)

## Expected files

```text
src/lettersign/
|-- cli.py                 # new command entrypoint
|-- config.py              # ProjectConfig + TOML round trip
|-- project.py             # project names and path resolution
|-- errors.py              # user-facing domain errors
`-- centerline.py          # existing algorithm; CLI ownership reduced

tests/
|-- test_config.py
|-- test_project.py
`-- test_cli.py
```

## Out of scope reminders

- No real watch loop yet.
- No SCAD data generation yet.
- No normalized black/red/green centerline SVG styling yet, except for whatever
  minimal project build wiring uses existing centerline output.
- No manual centerline/post reconciliation.

## Completion criteria

- `lettersign init <name>` creates the project directory/config safely.
- `lettersign build <name>` has a clear project-based behavior for M1, even if
  it delegates to the existing centerline renderer or stops before full M2
  pipeline work.
- Config updates are idempotent and preserve user values.
- Tests cover config, project paths, and the CLI surface.
- README accurately reflects implemented behavior.
- Verification commands pass locally.

## Notes

- **`tomlkit`** was added under Phase 2; Phase 4 did not need further dependency edits beyond pointing **`[project.scripts]`** at **`lettersign.cli:main`**.
- **README** documents project commands (`init`, `build`, `watch`), optional `-p` / `--projects-root`, TOML defaults, generated `<name>.centerline.svg` from the existing centerline renderer, reserved paths for later SCAD milestones, and legacy raw-SVG delegation.
- **`uv.lock`** was left unchanged when only the console script entry changed (no dependency churn).

## Decisions

- **Console entry**: Package installs invoke **`lettersign.cli:main`**. Legacy SVG usage is handled inside `cli.main` by delegating to `lettersign.centerline.main`.
- **Legacy CLI**: Non-subcommand invocations (e.g. a path to `.svg`) still delegate to the previous argparse-based centerline CLI so existing scripts keep working during the project-oriented transition.
- **`watch`**: Remains a stub that validates project/config resolution and states M4 for real watch behavior; no file-watch loop in M1.
- **`init`**: Creates project directory and TOML only; does not create `<name>.scad` yet (wrapper SCAD reserved for later milestones when generation exists).

