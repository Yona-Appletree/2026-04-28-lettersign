# Milestone 6: Integration validation and cleanup

## Goal

Validate the complete project workflow, clean up temporary scaffolding, and make
the roadmap implementation feel finished and maintainable.

## Suggested plan location

`docs/roadmaps/2026-04-28-lettersign-pipeline/m6-integration-validation-cleanup/`

Small plan: `plan.md`.

## Scope

### In scope

- Validate end-to-end workflows on fixture projects and at least one real
  project under `projects/`:
  - `lettersign init <name>`,
  - `lettersign build <name>`,
  - `lettersign watch <name>` smoke path,
  - config creation/update,
  - normalized centerline SVG output,
  - SCAD data/wrapper output.
- Review generated output for readability and style consistency.
- Clean up deprecated script-style entrypoints and temporary compatibility
  shims.
- Ensure tests cover config, project paths, SVG rendering, marker detection,
  SCAD generation, and key CLI flows.
- Update README/docs if behavior changed during implementation.
- Run and document verification commands:
  - `uv run ruff check .`,
  - `uv run ruff format --check .`,
  - `uv run pytest`,
  - `uv build`.

### Out of scope

- Manual edit reconciliation implementation.
- Advanced post geometry beyond the simple cylinder v0.
- Large CAD/mesh correctness validation.

## Key decisions

- Integration validation should test behavior structurally rather than relying
  on broad full-file golden outputs.
- Cleanup should remove scaffolding only after the end-to-end workflow is
  covered by tests.

## Deliverables

- Passing full local verification suite.
- Updated docs if needed.
- Cleanup of obsolete code paths.
- Summary of remaining deferred work, especially manual centerline/post
  reconciliation.

## Dependencies

- Depends on Milestones 1-5.

## Execution strategy

**Option B - Small plan (`/plan-small`).**

Justification: The milestone is validation-heavy and mostly deterministic, but
it spans the whole pipeline and benefits from a short checklist plan.

**Suggested chat opener:**

> I suggest we use the `/plan-small` process for this milestone, after
> which I will automatically implement. Agree?

