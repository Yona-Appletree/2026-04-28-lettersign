# AGENTS.md - lettersign Agent Instructions

## What lettersign Is

`lettersign` is tooling for building 3D-printable sign letters with
side-emitting addressable LED strip channels, mounting posts, and a backing
board workflow.

The core product is an iterative project pipeline:

```text
projects/<name>/<name>.svg
        |
        v
projects/<name>/<name>.toml
        |
        v
centerline SVG preview + OpenSCAD data
```

The user authors and edits the SVG. The tool derives LED centerlines, post
markers, and OpenSCAD geometry.

## Non-Negotiable Rules

- Preserve the user-owned/generated boundary:
  - user-owned: `<name>.svg`, `<name>.toml`, `<name>.scad`;
  - generated: `<name>.centerline.svg`, `<name>_data.scad`.
- Never overwrite `<name>.scad` after creating it.
- Update TOML by preserving user values/comments and adding missing defaults.
- Keep generated SVG/SCAD readable; these files are part of the design loop.
- Prefer explicit domain objects over loose dictionaries and stringly-typed
  plumbing.

## Code Style

- Use typed Python. Add type annotations to public functions and domain objects.
- Keep files small and single-purpose.
- Organize from most abstract to most mechanical:
  1. domain objects and invariants,
  2. pipeline orchestration,
  3. renderers/adapters,
  4. utilities.
- Avoid utility-first design. Do not create a generic helper until a concrete
  domain need exists.
- Make errors actionable. Prefer clear project/config/SVG validation messages
  over generic tracebacks for expected user mistakes.
- Keep comments rare and useful: explain non-obvious geometry, SVG, or SCAD
  reasoning.

## Project Structure Direction

The roadmap target is:

```text
src/lettersign/
|-- cli.py
|-- project.py
|-- config.py
|-- svg_input.py
|-- geometry.py
|-- centerline.py
|-- markers.py
|-- render_svg.py
|-- render_scad.py
|-- scad/
|   `-- lettersign_common.scad
`-- errors.py
```

Do not treat this tree as mandatory all at once. Let milestones introduce files
when they earn their place.

## Geometry and Units

- Config and OpenSCAD dimensions are in millimeters.
- Use SVG physical metadata for scale when available.
- If SVG metadata does not provide scale, assume `1 SVG unit = 1 mm`.
- Default OpenSCAD-facing coordinates to a lower-left oriented coordinate space.

## SCAD Style

- Follow the user's existing OpenSCAD style: readable arrays, explicit modules,
  section separators, and user-editable top-level wrappers.
- Put generated per-project geometry in `<name>_data.scad`.
- Put shared helpers, such as post modules, in common SCAD files.
- Create per-path modules like `path1_outline`, `path1_channel`,
  `path1_posts`, and `path1_3d()`.

## Testing and Validation

Use layered tests:

- unit tests for config, project paths, unit conversion, and geometry;
- renderer tests for SVG/SCAD structure and generated-file headers;
- fixture integration tests using tiny SVG projects;
- minimal timeout-bound watch tests only.

Run before committing:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

## Roadmap

The active design roadmap is:

`docs/roadmaps/2026-04-28-lettersign-pipeline/`

Use it as the source of truth for milestone scope and deferred decisions,
especially manual post/centerline edit reconciliation.

