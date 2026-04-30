# Phase 7: Cleanup, review, and validation

## Scope of phase

Perform final cleanup and validation for M2.

In scope:

- Remove temporary code, stale comments, unused compatibility helpers, and
  debug artifacts introduced during M2.
- Ensure `centerline.py` no longer owns project rendering; legacy raw SVG
  rendering may remain for compatibility.
- Ensure README and plan summary are accurate.
- Add `summary.md` for this full roadmap plan.
- Run full validation.

Out of scope:

- Do not add new features.
- Do not implement SCAD generation.
- Do not implement watch mode.

## Code organization reminders

- Keep modules small and single-purpose.
- Prefer domain/pipeline entry points over utility sprawl.
- Leave no unexplained TODOs.

## Sub-agent reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings.
- Do not skip or weaken tests.
- Report files changed, validation commands/results, and deviations.

## Implementation details

Read all M2 phase files and inspect the final diff.

Cleanup checklist:

- Search for temporary markers:
  - `TODO`
  - `debug`
  - `pdb`
  - commented-out code
  - accidental scratch files.
- Check new public functions have type annotations.
- Check generated SVG tests assert structure/styles without brittle full-file
  goldens.
- Check raw SVG legacy CLI tests still pass.
- Check `lettersign build <name>` produces normalized output through the
  pipeline.
- Check docs accurately state implemented M2 behavior.

Create `summary.md` in this plan directory with:

```markdown
### What was built

- ...

### Decisions for future reference

#### ...
```

Only record decisions that are useful later. Include at least:

- `5 mm` preview marker radius is a named constant, not user config.
- Project build uses `line_resolution` for flattening; legacy CLI keeps presets.
- Structural SVG tests over full-file goldens.

## Validate

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

