# Milestone 3: SCAD generation foundation

## Goal

Generate readable OpenSCAD data and wrapper files for each project, using the
original outlines, derived centerline channels, and post marker geometry.

## Suggested plan location

`docs/roadmaps/2026-04-28-lettersign-pipeline/m3-scad-generation-foundation/`

Full plan: `00-notes.md`, `00-design.md`, numbered phase files.

## Scope

### In scope

- Add shared SCAD helper file for common modules such as posts.
- Generate `projects/<name>/<name>_data.scad` on each build.
- Create `projects/<name>/<name>.scad` only if absent, importing/invoking the
  generated data file.
- For each path in the original SVG, generate modules such as:
  - `path1_outline`,
  - `path1_channel`,
  - `path1_posts`,
  - `path1_3d()`.
- Represent outlines from original SVG paths.
- Derive channel geometry by stroking centerline paths with round ends using
  `led_channel_width` and `line_resolution`.
- Represent posts as simple cylinders using `post_height`.
- Follow the user's existing SCAD style: readable arrays, explicit modules,
  section separators, stable helper files, and user-editable wrappers.
- Add tests asserting SCAD module names, includes, generated-file headers, and
  high-level geometry structure.
- Keep `README.md` current with implemented SCAD output files, module names, and
  customization boundaries.

### Out of scope

- Sophisticated post design.
- Manual edit reconciliation.
- Print-ready optimization for every SVG edge case.
- OpenSCAD rendering or mesh validation in CI unless it is cheap and reliable.

## Key decisions

- `<name>_data.scad` is generated and overwritten.
- `<name>.scad` is user-owned and never overwritten after creation.
- SCAD output should be human-readable, not a compact opaque dump.
- Shared helpers live outside per-project generated data.

## Deliverables

- `src/lettersign/render_scad.py` or equivalent SCAD renderer.
- `src/lettersign/scad/lettersign_common.scad`.
- Generated project wrapper template.
- Fixture integration tests for generated SCAD structure.
- README updates for SCAD generation behavior and the wrapper/data split.

## Dependencies

- Depends on Milestone 1 project/config foundation.
- Depends on Milestone 2 pipeline/domain output for outlines, centerlines, and
  markers.

## Execution strategy

**Option C - Full plan (`/plan`).**

Justification: This milestone introduces the CAD-facing data contract and
generated/user-owned split. It needs a design pass for module naming, coordinate
data representation, helper file placement, and channel polygon generation.

**Suggested chat opener:**

> This milestone needs a full plan. I'll run the `/plan` process -
> question iteration, design, then phase files - and then `/implement`
> to dispatch. Agree?

