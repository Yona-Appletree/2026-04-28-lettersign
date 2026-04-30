# Phase 3: Marker detection

## Scope of phase

Implement endpoint and intersection marker detection for centerline geometry.

In scope:

- Add `src/lettersign/markers.py`.
- Add a named static marker radius constant, `PREVIEW_MARKER_RADIUS_MM = 5.0`,
  in `config.py` or another obvious constants location.
- Detect markers at centerline endpoints and intersections/branch points.
- Deduplicate nearby markers with a small tolerance.
- Add marker tests.

Out of scope:

- Do not render SVG.
- Do not wire pipeline/CLI.
- Do not add marker radius to user TOML config.
- Do not implement manual edit reconciliation.

## Code organization reminders

- Public marker dataclasses or return types should be abstract and typed.
- Keep Shapely-specific helper functions lower in the file.
- Avoid broad changes to `centerline.py` or `svg_input.py`.

## Sub-agent reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- If marker topology gets unexpectedly complex, implement the simple documented
  behavior and report limitations.
- Report files changed, validation commands/results, and deviations.

## Implementation details

Read:

- `src/lettersign/geometry.py`
- `src/lettersign/centerline.py`
- M2 `00-design.md`

Create `src/lettersign/markers.py` with a public function like:

```python
def detect_markers(centerline: BaseGeometry, *, tolerance: float = 1e-6) -> tuple[Marker, ...]:
    ...
```

`Marker` may live in `geometry.py` or `markers.py`; prefer `geometry.py` if it
is part of the shared domain. It should include at least:

- point/position,
- radius in mm (use `PREVIEW_MARKER_RADIUS_MM`),
- optional kind string such as `"endpoint"` / `"intersection"` if useful.

Detection behavior:

- For each `LineString`, add first and last coordinate as endpoint markers.
- For `MultiLineString` and `GeometryCollection`, traverse line parts.
- Detect intersections/branch points among line segments/line strings:
  - If a point appears in 3+ segment endpoints, mark it as an intersection.
  - If Shapely intersection between line parts yields a point, mark it.
  - Keep this simple and deterministic; do not overfit complex overlaps.
- Deduplicate markers by distance/tolerance so endpoints that are also branch
  points do not duplicate visually.

Tests:

- `tests/test_markers.py`
- A simple `LineString([(0, 0), (10, 0)])` gives two endpoint markers.
- A T junction made from multiple line strings gives marker(s) at branch and
  ends.
- Duplicate coincident points are deduplicated.
- Marker radius equals the named `5.0` constant.

## Validate

Run:

```bash
uv run pytest tests/test_markers.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

