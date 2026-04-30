# Phase 6: README/docs update for normalized output

## Scope of phase

Update user-facing docs for the implemented M2 normalized centerline SVG
behavior.

In scope:

- Update `README.md` to describe M2 output styles and current pipeline behavior.
- Mention that `lettersign build <name>` now produces a normalized preview:
  black outlines, red centerline, green 5 mm markers.
- Preserve notes that SCAD generation and real watch mode are later milestones.

Out of scope:

- Do not change code unless a doc command is wrong and requires a tiny
  correction.
- Do not update unrelated roadmap files except if needed for consistency.

## Code organization reminders

- Keep README concise and accurate.
- Distinguish implemented behavior from future roadmap behavior.
- Avoid markdown tables unless truly helpful.

## Sub-agent reminders

- Do not commit.
- Do not expand scope.
- Do not edit code unless necessary to correct a documented command.
- Report files changed, validation commands/results, and deviations.

## Implementation details

Read:

- `README.md`
- `AGENTS.md`
- M2 `00-design.md`
- Current implemented modules after phases 1-5.

README should include:

- Project CLI commands remain:
  - `uv run lettersign init myletter`
  - `uv run lettersign build myletter`
  - `uv run lettersign watch myletter`
- M2 build output:
  - `<name>.centerline.svg`
  - black outline/no fill,
  - red centerline with `led_channel_width`,
  - green circular post markers with radius 5 mm.
- Config defaults and meaning stay accurate.
- SCAD files remain reserved for later milestones.
- Legacy raw SVG invocation remains available.

## Validate

Run:

```bash
uv run ruff check .
uv run pytest -v
```

