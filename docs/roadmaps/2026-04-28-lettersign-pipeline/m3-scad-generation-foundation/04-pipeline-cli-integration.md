# Phase 4: Pipeline and CLI build integration

## Scope of phase

Wire SCAD geometry/rendering into `lettersign build <name>`.

In scope:

- Update `src/lettersign/pipeline.py` so project build writes:
  - `<name>.centerline.svg`,
  - `<name>_data.scad`,
  - `<name>.scad` only if absent,
  - projects-root `lettersign_common.scad`.
- Preserve existing normalized SVG behavior.
- Preserve missing-SVG and invalid-SVG error behavior.
- Add/extend pipeline and CLI tests for SCAD outputs.

Out of scope:

- Do not implement watch mode.
- Do not run OpenSCAD.
- Do not add config keys.
- Do not change legacy raw SVG CLI behavior.

## Code Organization Reminders

- Keep `pipeline.py` orchestration-only; geometry stays in `scad_geometry.py`,
  rendering/file policies stay in `render_scad.py`.
- Keep generated/user-owned boundaries explicit.
- Add focused tests; avoid broad golden snapshots.
- Temporary code must have a TODO comment so cleanup can find it.

## Sub-agent Reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- If prior phase APIs differ slightly, adapt locally without rewriting whole
  modules.
- Report files changed, validation commands/results, and deviations.

## Implementation Details

Read:

- `src/lettersign/pipeline.py`
- `src/lettersign/scad_geometry.py`
- `src/lettersign/render_scad.py`
- `src/lettersign/cli.py`
- `tests/test_pipeline.py`
- `tests/test_cli.py`

Update pipeline:

- Existing `build_centerline_preview(paths, config)` may be renamed only if
  tests/CLI are updated and the name remains clear. Prefer keeping the function
  name if that avoids churn, even though it now writes more outputs.
- After computing:
  - `svg_input`,
  - `geom = generate_centerline_geometry(...)`,
  - `markers = detect_markers(...)`,
  call `build_scad_model(...)`.
- After writing the centerline SVG, call `write_scad_outputs(paths, model)`.
- Return `paths.centerline_svg` as before unless a broader return object already
  exists. Keep CLI output simple.

Tests:

- Extend `tests/test_pipeline.py`:
  - `build_centerline_preview()` writes data SCAD, wrapper SCAD, and common SCAD.
  - data SCAD contains `module path1_outline()`, `module path1_channel()`,
    `module path1_posts()`, `module path1_3d()`, `use <../lettersign_common.scad>`.
  - wrapper contains `use <demo_data.scad>` and `demo_3d();`.
  - existing wrapper contents are preserved on rebuild.
- Extend `tests/test_cli.py`:
  - `lettersign build demo` creates SCAD outputs as well as centerline SVG.
  - Legacy raw SVG invocation still writes legacy debug SVG and does not require
    project SCAD outputs.

## Validate

Run:

```bash
uv run pytest tests/test_pipeline.py tests/test_cli.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

