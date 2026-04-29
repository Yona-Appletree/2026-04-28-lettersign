# Milestone 1: Project/config/CLI foundation

## Goal

Establish the project-oriented command surface and typed configuration layer so
`lettersign` operates on `projects/<name>/` instead of raw SVG paths.

## Suggested plan location

`docs/roadmaps/2026-04-28-lettersign-pipeline/m1-project-config-cli-foundation/`

Small plan: `plan.md`.

## Scope

### In scope

- Add `lettersign init <name>`, `lettersign build <name>`, and
  `lettersign watch <name>` command shape.
- Resolve project paths:
  - `projects/<name>/<name>.svg`,
  - `projects/<name>/<name>.toml`,
  - `projects/<name>/<name>.centerline.svg`,
  - `projects/<name>/<name>_data.scad`,
  - `projects/<name>/<name>.scad`.
- Add `ProjectConfig` with defaults:
  - `height = 15`,
  - `led_channel_width = 3`,
  - `post_height = 12`,
  - `line_resolution = 0.25`.
- Add `tomlkit` and schema-managed config read/update/write behavior.
- Add user-facing validation errors for missing/invalid project inputs.
- Add focused tests for config defaults, config update behavior, and project
  path resolution.
- Keep `README.md` current with any implemented CLI/config behavior.

### Out of scope

- Watch loop implementation beyond CLI shape/stub behavior.
- SCAD generation.
- Normalized centerline SVG style changes beyond whatever wiring is needed for
  `build`.
- Manual centerline/post reconciliation.

## Key decisions

- The CLI is command-first: `init`, `build`, `watch`.
- Project config is user-owned but schema-managed: preserve values and add
  missing defaults.
- `tomlkit` owns TOML round-tripping; `ProjectConfig` remains a typed domain
  object independent of TOML document details.

## Deliverables

- `src/lettersign/cli.py` command entrypoint.
- `src/lettersign/project.py` project path/domain helpers.
- `src/lettersign/config.py` typed config and TOML update layer.
- Updated console script in `pyproject.toml`.
- Unit tests for config and project path behavior.
- README updates for implemented `init`/`build` command behavior and config
  defaults.

## Dependencies

- Does not depend on later milestones.
- Builds on the existing `lettersign` package layout and uv/pytest/Ruff setup.

## Execution strategy

**Option B - Small plan (`/plan-small`).**

Justification: The milestone is mostly clear but touches CLI behavior, config
round-tripping, a new dependency, and user-facing error conventions.

**Suggested chat opener:**

> I suggest we use the `/plan-small` process for this milestone, after
> which I will automatically implement. Agree?

