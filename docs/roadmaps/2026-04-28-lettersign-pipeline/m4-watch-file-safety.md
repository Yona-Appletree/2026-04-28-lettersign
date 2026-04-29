# Milestone 4: Watch mode and generated/user-owned file safety

## Goal

Make the iterative workflow smooth and safe: `lettersign watch <name>` should
refresh generated outputs as inputs change while respecting user-owned files.

## Suggested plan location

`docs/roadmaps/2026-04-28-lettersign-pipeline/m4-watch-file-safety/`

Small plan: `plan.md`.

## Scope

### In scope

- Implement `lettersign watch <name>` to monitor the project SVG and TOML
  config.
- Rebuild generated centerline SVG and `_data.scad` when watched inputs change.
- Keep `<name>.scad` user-owned: create only if missing, never overwrite.
- Keep `<name>.toml` user-owned but schema-managed: add missing defaults without
  replacing existing values.
- Add clear generated-file headers to generated SVG/SCAD outputs.
- Add debounce/error reporting so transient save states do not make watch mode
  noisy.
- Add a minimal, reliable watch-mode smoke test.
- Keep `README.md` current with implemented watch behavior and file safety
  guarantees.

### Out of scope

- Manual post/centerline reconciliation.
- Watching OpenSCAD output files.
- Complex multi-project watch orchestration.

## Key decisions

- Build/watch may overwrite generated outputs only.
- User-owned files are protected by default, with no destructive force mode in
  the initial watch milestone unless needed.
- Watch-mode tests should be minimal and timeout-bound to avoid flaky CI.

## Deliverables

- Functional `lettersign watch <name>` command.
- Generated-file headers in SVG/SCAD outputs.
- Tests for user-owned file protection and watch smoke behavior.
- Improved CLI error messages for watch/build failures.
- README updates for `watch` usage and generated/user-owned file policy.

## Dependencies

- Depends on Milestone 1 CLI/project/config foundation.
- Depends on Milestone 2 generated SVG pipeline.
- Depends on Milestone 3 generated SCAD data.

## Execution strategy

**Option B - Small plan (`/plan-small`).**

Justification: The behavior is well-scoped, but watch loops need careful
debouncing, error reporting, and CI-safe tests.

**Suggested chat opener:**

> I suggest we use the `/plan-small` process for this milestone, after
> which I will automatically implement. Agree?

