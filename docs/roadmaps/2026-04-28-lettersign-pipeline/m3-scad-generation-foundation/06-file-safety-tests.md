# Phase 6: Wrapper/common/data file safety tests

## Scope of phase

Add focused tests around generated/user-owned SCAD file safety and shared helper
behavior.

In scope:

- Add or strengthen tests that data SCAD and common SCAD are overwritten.
- Add or strengthen tests that wrapper SCAD is created only if missing and is
  preserved if edited.
- Add tests for relative `use` paths.
- Add tests for package build/resource inclusion if not already covered.

Out of scope:

- Do not add new SCAD features.
- Do not change renderer/geometry behavior except for small fixes needed to make
  the safety contract true.
- Do not run OpenSCAD.

## Code Organization Reminders

- Keep tests focused on ownership semantics and high-level structure.
- Avoid full-file golden snapshots.
- Use temp directories; do not write into real `projects/` fixtures.
- Temporary code must have a TODO comment so cleanup can find it.

## Sub-agent Reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- If a safety test reveals a real implementation mismatch, make the smallest
  fix in the relevant module and report it clearly.
- Report files changed, validation commands/results, and deviations.

## Implementation Details

Read:

- `src/lettersign/render_scad.py`
- `src/lettersign/pipeline.py`
- `src/lettersign/project.py`
- `tests/test_render_scad.py`
- `tests/test_pipeline.py`

Tests to add or strengthen:

- In renderer tests:
  - `write_scad_outputs()` overwrites data SCAD if stale content exists.
  - `write_scad_outputs()` overwrites common SCAD if stale content exists.
  - `write_scad_outputs()` does not overwrite an existing wrapper containing
    custom text.
  - A newly created wrapper contains `use <demo_data.scad>` and `demo_3d();`.
- In pipeline tests:
  - Running build twice preserves custom wrapper contents while refreshing data
    SCAD.
  - `projects/lettersign_common.scad` is at the projects root, not inside
    `projects/<name>/`.
- In package/resource tests:
  - canonical common helper text is loadable through the package resource API.
  - `uv build` should include the `.scad` helper by virtue of package-data
    config; direct archive inspection is optional unless cheap.

## Validate

Run:

```bash
uv run pytest tests/test_render_scad.py tests/test_pipeline.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv build
```

