# Phase 1: Project path and shared helper foundation

## Scope of phase

Create the foundation for a single shared OpenSCAD helper file at the projects
root.

In scope:

- Add `ProjectPaths.common_scad` pointing to `projects_root / "lettersign_common.scad"`.
- Add a canonical helper file at `src/lettersign/scad/lettersign_common.scad`.
- Add a small Python API to read/render/write the common helper if needed by
  later phases.
- Ensure package data includes the `.scad` helper in builds.
- Add tests for path resolution and helper file availability.

Out of scope:

- Do not render project data SCAD yet.
- Do not wire `lettersign build` to write SCAD files yet.
- Do not create per-project copies of `lettersign_common.scad`.
- Do not add new config keys.

## Code Organization Reminders

- Prefer granular files, one concept per file.
- Put public entry points and tests first, helpers lower in the file.
- Keep shared helper ownership explicit: canonical source in package, generated
  shared output at the projects root.
- Temporary code must have a TODO comment so cleanup can find it.

## Sub-agent Reminders

- Do not commit. The plan commits at the end as a single unit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- If package-data handling is ambiguous, use the smallest setuptools-supported
  configuration and report the choice.
- Report files changed, validation commands/results, and deviations.

## Implementation Details

Read:

- `src/lettersign/project.py`
- `pyproject.toml`
- M3 `00-notes.md` and `00-design.md`

Update `src/lettersign/project.py`:

- Add `common_scad: Path` to `ProjectPaths`.
- In `resolve_project()`, set `common_scad=root / "lettersign_common.scad"`.
- Existing path tests should continue passing.

Add canonical helper:

- Create `src/lettersign/scad/lettersign_common.scad`.
- Keep it small and stable. It should include helper modules for the M3 renderer,
  for example:

```scad
// Shared OpenSCAD helpers for lettersign generated files.

module lettersign_post(position, radius, height) {
  translate([position[0], position[1], 0])
    cylinder(r=radius, h=height);
}
```

If you add a channel/outline helper, keep it simple and documented. The exact
module names must be stable and tested.

Add helper-loading API:

- Prefer adding a small function to `src/lettersign/render_scad.py` only if that
  file is created in this phase; otherwise create `src/lettersign/scad_assets.py`
  with:

```python
def common_scad_text() -> str:
    ...
```

- Use `importlib.resources.files("lettersign.scad")` or equivalent, not a
  hard-coded source-tree path.
- If creating `lettersign/scad/`, add `__init__.py` if needed for resource
  access.

Package data:

- Update `pyproject.toml` so `src/lettersign/scad/*.scad` is included in
  package builds. With setuptools, this can be done with
  `[tool.setuptools.package-data]`.

Tests:

- Update `tests/test_project.py` to assert `resolve_project("demo",
  projects_root=root).common_scad == root / "lettersign_common.scad"`.
- Add or update a test to assert `common_scad_text()` contains
  `module lettersign_post`.

## Validate

Run:

```bash
uv run pytest tests/test_project.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv build
```

