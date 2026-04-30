# Phase 5: Project pipeline and CLI build integration

## Scope of phase

Wire the M2 domain/input/centerline/marker/renderer modules into
`lettersign build <name>`.

In scope:

- Add `src/lettersign/pipeline.py`.
- Make `cli.cmd_build` call the project pipeline instead of manually building a
  legacy centerline namespace.
- Use `ProjectConfig.line_resolution` for SVG path flattening.
- Use `ProjectConfig.led_channel_width` for preview centerline stroke width.
- Write `paths.centerline_svg`.
- Add project pipeline/CLI integration tests.

Out of scope:

- Do not implement SCAD output.
- Do not implement watch mode.
- Do not remove raw SVG legacy compatibility.
- Do not implement manual centerline/post reconciliation.

## Code organization reminders

- Keep `pipeline.py` as orchestration, not a dumping ground for algorithm
  helpers.
- Public API first; file write helpers lower.
- Maintain user-facing errors via `LettersignError` subclasses where practical.

## Sub-agent reminders

- Do not commit.
- Do not expand scope.
- Do not weaken tests.
- If module APIs from earlier phases differ from this phase file, adapt locally
  if obvious; otherwise stop and report.
- Report files changed, validation commands/results, and deviations.

## Implementation details

Read:

- `src/lettersign/cli.py`
- `src/lettersign/project.py`
- `src/lettersign/config.py`
- `src/lettersign/svg_input.py`
- `src/lettersign/centerline.py`
- `src/lettersign/markers.py`
- `src/lettersign/render_svg.py`

Create `src/lettersign/pipeline.py` with a public function like:

```python
def build_centerline_preview(paths: ProjectPaths, config: ProjectConfig) -> Path:
    ...
```

Behavior:

1. Require `paths.input_svg` to exist. Either keep this check in `cli.cmd_build`
   or move it into pipeline, but errors must remain actionable.
2. Load normalized SVG input with `line_resolution=config.line_resolution`.
3. Generate outline and centerline geometry.
4. Detect markers.
5. Render normalized SVG using `config.led_channel_width`.
6. Ensure output directory exists and write `paths.centerline_svg`.
7. Return the output path.

Update `cli.py`:

- `cmd_build` should still create/update config first.
- It should delegate project generation to pipeline.
- It can print a concise success message including the output path.
- Legacy non-subcommand raw SVG behavior must still work.

Tests:

- Add `tests/test_pipeline.py` or extend `tests/test_cli.py`.
- Use a temp project root and a minimal SVG.
- Assert `lettersign build <name>` writes normalized SVG with:
  - black outline/no fill,
  - red centerline,
  - green circles.
- Assert missing SVG still exits nonzero with a useful message.
- Assert legacy raw SVG invocation still writes the old debug output.

## Validate

Run:

```bash
uv run pytest tests/test_pipeline.py tests/test_cli.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

