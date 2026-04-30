# Phase 5: README/docs update

## Scope of phase

Update user-facing docs for implemented M3 SCAD generation behavior.

In scope:

- Update `README.md` to describe SCAD outputs from `lettersign build <name>`.
- Document generated vs user-owned boundaries.
- Document the shared `projects/lettersign_common.scad` helper.
- Mention per-path module names and the first-pass nature of `pathN_3d()`.

Out of scope:

- Do not change code.
- Do not update unrelated roadmap milestones unless there is a direct
  inconsistency.
- Do not document future watch/manual-edit behavior as implemented.

## Code Organization Reminders

- Keep docs concise and accurate.
- Distinguish implemented behavior from later milestones.
- Use ASCII-only markdown in this repo.
- Avoid broad tables unless they add real clarity.

## Sub-agent Reminders

- Do not commit.
- Do not expand scope.
- Do not edit code.
- Report files changed, validation commands/results, and deviations.

## Implementation Details

Read:

- `README.md`
- M3 `00-design.md`
- Current implemented SCAD modules after phases 1-4

README updates should cover:

- `lettersign build <name>` now writes:
  - `<name>.centerline.svg`,
  - `<name>_data.scad`,
  - `<name>.scad` only if missing,
  - `projects/lettersign_common.scad`.
- Generated/user-owned boundaries:
  - generated/overwritten: centerline SVG, data SCAD, common SCAD helper,
  - user-owned/preserved: input SVG, TOML values/comments, wrapper SCAD.
- Per-path modules:
  - `path1_outline()`,
  - `path1_channel()`,
  - `path1_posts()`,
  - `path1_3d()`.
- The generated top-level module such as `<name>_3d()`.
- M3 geometry limitations:
  - posts are simple cylinders,
  - channel is generated from buffered centerline clipped per source path,
  - print-ready refinements/manual reconciliation are future work.

## Validate

Run:

```bash
uv run ruff check .
uv run pytest -v
```

