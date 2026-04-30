# Milestone 2: Pipeline domain split and normalized centerline SVG

## Goal

Extract the current centerline script into typed, testable pipeline modules and
produce normalized centerline SVG output with outlines, centerlines, and marker
posts rendered in consistent styles.

## Suggested plan location

`docs/roadmaps/2026-04-28-lettersign-pipeline/m2-pipeline-domain-normalized-svg/`

Full plan: `00-notes.md`, `00-design.md`, numbered phase files.

## Scope

### In scope

- Split `src/lettersign/centerline.py` into small single-purpose modules for:
  - SVG input parsing and metadata/unit scale handling,
  - geometry/domain objects,
  - centerline computation,
  - endpoint/intersection marker detection,
  - normalized centerline SVG rendering,
  - pipeline orchestration used by `build`.
- Normalize generated SVG style:
  - original outlines are black stroke with no fill,
  - centerlines are red,
  - posts/markers are green circles,
  - unneeded source SVG styling is stripped.
- Use SVG metadata for physical unit scale when available; otherwise assume
  `1 SVG unit = 1 mm`.
- Use lower-left oriented coordinates for downstream OpenSCAD-facing geometry.
- Add tests for SVG unit conversion, path/domain conversion, marker detection,
  and rendered SVG structure.
- Keep `README.md` current with normalized SVG output behavior as implemented.

### Out of scope

- SCAD generation.
- Watch implementation.
- Manual edit reconciliation for posts/centerlines.
- Advanced centerline pruning beyond existing options and marker detection.

## Key decisions

- Millimeters are the internal/output unit for geometry after SVG ingestion.
- Generated centerline SVG is treated as regenerable in v0.
- Structural renderer tests are preferred over large full-file goldens.
- Centerline code should no longer own CLI parsing.

## Deliverables

- Refactored pipeline modules under `src/lettersign/`.
- `build` command wired to project SVG/config and normalized SVG output.
- Unit and fixture tests for centerline pipeline behavior.
- Removal or narrowing of script-style responsibilities in
  `lettersign.centerline`.
- README updates for generated centerline SVG styling and project build output.

## Dependencies

- Depends on Milestone 1 project/config/CLI foundation.

## Execution strategy

**Option C - Full plan (`/plan`).**

Justification: This milestone refactors the existing core algorithm while adding
domain boundaries, unit handling, marker detection, rendering semantics, and
fixture tests. It needs a design pass to avoid losing behavior during the split.

**Suggested chat opener:**

> This milestone needs a full plan. I'll run the `/plan` process -
> question iteration, design, then phase files - and then `/implement`
> to dispatch. Agree?

