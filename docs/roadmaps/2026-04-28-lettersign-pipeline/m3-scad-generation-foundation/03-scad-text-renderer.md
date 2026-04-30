# Phase 3: SCAD text renderer

## Scope of phase

Render the SCAD model into readable generated data, wrapper, and shared helper
outputs.

In scope:

- Add `src/lettersign/render_scad.py`.
- Render `<name>_data.scad` text from `ScadModel`.
- Render `<name>.scad` wrapper text.
- Provide file-writing helpers for generated data, user-owned wrapper, and
  projects-root common helper.
- Add tests for module names, `use` paths, generated headers, wrapper
  preservation, and key config values.

Out of scope:

- Do not build SCAD geometry.
- Do not wire pipeline/CLI.
- Do not run OpenSCAD or validate meshes.
- Do not overwrite an existing wrapper.

## Code Organization Reminders

- Keep text rendering in `render_scad.py`; do not mix it into geometry code.
- Public render/write APIs first; formatting helpers lower in the file.
- Make generated/user-owned file policies explicit in function names.
- Favor readable, stable output over compact output.
- Temporary code must have a TODO comment so cleanup can find it.

## Sub-agent Reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- If the `ScadModel` API from Phase 2 differs slightly, adapt to the existing
  dataclasses rather than rewriting the geometry layer.
- Report files changed, validation commands/results, and deviations.

## Implementation Details

Read:

- `src/lettersign/scad_geometry.py`
- `src/lettersign/project.py`
- Phase 1 helper-loading API (if present)
- M3 `00-design.md`

Create `src/lettersign/render_scad.py` with public APIs similar to:

```python
def render_data_scad(model: ScadModel) -> str: ...
def render_wrapper_scad(project_name: str) -> str: ...
def write_scad_outputs(paths: ProjectPaths, model: ScadModel) -> None: ...
```

`write_scad_outputs()` behavior:

- Always write/overwrite `paths.common_scad` from the canonical common helper
  text.
- Always write/overwrite `paths.data_scad` from `render_data_scad(model)`.
- Create `paths.wrapper_scad` only if it does not exist.
- Do not modify wrapper contents if the file already exists.

Generated data SCAD requirements:

- Start with a generated-file header comment.
- Include/use the shared helper from the project directory:

```scad
use <../lettersign_common.scad>
```

- Include project constants such as:
  - `<name>_height = ...;`
  - `<name>_led_channel_width = ...;`
  - `<name>_post_height = ...;`
- For every `ScadPathPart`, include modules:
  - `module path1_outline() { ... }`
  - `module path1_channel() { ... }`
  - `module path1_posts() { ... }`
  - `module path1_3d() { ... }`
- Include a top-level module such as `module <name>_3d() { path1_3d(); ... }`.
- Render polygons with `polygon(points=..., paths=...)`.
- Render posts using the shared helper, e.g.:

```scad
lettersign_post([x, y], radius, height);
```

- `pathN_3d()` should be readable first-pass geometry:

```scad
module path1_3d() {
  union() {
    difference() {
      linear_extrude(height=project_height)
        path1_outline();
      translate([0, 0, -0.1])
        linear_extrude(height=project_height + 0.2)
          path1_channel();
    }
    path1_posts();
  }
}
```

Exact variable names can vary; tests should assert key structure, not full text.

Wrapper SCAD requirements:

- Start with a user-owned/customizable comment, not a generated overwrite warning.
- Use project data:

```scad
use <<name>_data.scad>
```

- Invoke `<name>_3d();` by default.

Formatting helpers:

- Format floats deterministically, e.g. `"{value:.6g}"`.
- Render arrays across lines for readability.

Tests:

- Add `tests/test_render_scad.py`.
- Build a small `ScadModel` by hand.
- Assert data text contains:
  - generated header,
  - `use <../lettersign_common.scad>`,
  - `module path1_outline()`,
  - `module path1_channel()`,
  - `module path1_posts()`,
  - `module path1_3d()`,
  - `module demo_3d()`,
  - `polygon(points=`,
  - `lettersign_post(`,
  - config values.
- Assert wrapper text contains `use <demo_data.scad>` and `demo_3d();`.
- Test `write_scad_outputs()` preserves an existing wrapper while rewriting data
  and common helper.

## Validate

Run:

```bash
uv run pytest tests/test_render_scad.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

