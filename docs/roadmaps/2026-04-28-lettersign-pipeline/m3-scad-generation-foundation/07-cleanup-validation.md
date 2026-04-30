# Phase 7: Cleanup, review, and validation

## Scope of phase

Perform final M3 cleanup and validation.

In scope:

- Remove temporary code, stale comments, debug artifacts, and unused helpers.
- Ensure generated/user-owned SCAD boundaries match the design.
- Ensure README and M3 plan summary are accurate.
- Create `summary.md` for this plan.
- Run full validation.

Out of scope:

- Do not add new features.
- Do not implement watch mode.
- Do not run OpenSCAD.
- Do not add new config keys.

## Code Organization Reminders

- Keep modules small and single-purpose.
- Keep SCAD geometry, SCAD rendering, and pipeline orchestration separate.
- Keep public APIs typed.
- Leave no unexplained TODOs.

## Sub-agent Reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings.
- Do not skip or weaken tests.
- Report files changed, validation commands/results, and deviations.

## Implementation Details

Read all M3 phase files and inspect the full current diff.

Cleanup checklist:

- Search for temporary markers:
  - `TODO`
  - `debug` except intentional legacy debug wording,
  - `pdb`,
  - commented-out code,
  - scratch files.
- Check `ProjectPaths.common_scad` resolves to the projects root.
- Check common helper is one shared helper at `projects/lettersign_common.scad`,
  not copied into every project directory.
- Check `<name>_data.scad` is generated/overwritten.
- Check `<name>.scad` is created only if absent.
- Check generated data uses `use <../lettersign_common.scad>`.
- Check wrapper uses `use <<name>_data.scad>`.
- Check `pathN_outline`, `pathN_channel`, `pathN_posts`, and `pathN_3d` module
  names exist in generated data.
- Check README states implemented behavior accurately.
- Check tests are structural and not broad full-file goldens.

Create `summary.md` in this plan directory with:

```markdown
### What was built

- ...

### Decisions for future reference

#### ...
```

Record only useful future decisions, including:

- The common SCAD helper lives once at the projects root.
- Wrapper SCAD is user-owned and preserved.
- Per-path channels are clipped from the global buffered centerline for M3.

## Validate

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

