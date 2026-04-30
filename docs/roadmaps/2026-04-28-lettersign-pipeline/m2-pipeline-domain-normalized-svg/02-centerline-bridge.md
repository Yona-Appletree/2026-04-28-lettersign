# Phase 2: Centerline algorithm extraction and bridge

## Scope of phase

Make `centerline.py` usable as an algorithm module for the project pipeline
without breaking the legacy raw SVG CLI.

In scope:

- Add typed public functions that accept normalized SVG/domain input and return
  Shapely outline/centerline geometry suitable for M2.
- Move or narrow debug-rendering ownership so project rendering can live in
  `render_svg.py` later.
- Keep `lettersign path/to/file.svg ...` legacy behavior working.
- Add tests for the centerline bridge with small SVG/domain inputs.

Out of scope:

- Do not implement marker detection.
- Do not implement normalized renderer.
- Do not wire `cli.build` yet.
- Do not change pygeoops algorithm defaults except as needed to use
  `ProjectConfig.line_resolution` for project builds.

## Code organization reminders

- Prefer small public functions with typed parameters and return values.
- Keep algorithm code in `centerline.py`; do not move everything in one risky
  pass.
- Place entry points near the top, helper functions near the bottom.
- Keep raw CLI compatibility isolated.

## Sub-agent reminders

- Do not commit.
- Do not expand scope.
- Do not weaken or skip tests.
- If the existing algorithm cannot consume Phase 1 domain objects cleanly, stop
  and report instead of inventing a broad redesign.
- Report files changed, validation commands/results, and deviations.

## Implementation details

Read:

- `src/lettersign/geometry.py`
- `src/lettersign/svg_input.py`
- `src/lettersign/centerline.py`
- M2 `00-notes.md` and `00-design.md`

Target API shape:

- A project-facing function in `centerline.py`, for example:

```python
@dataclass(frozen=True)
class CenterlineGeometry:
    outline: Polygon | MultiPolygon
    centerline: LineString | MultiLineString | GeometryCollection

def generate_centerline_geometry(
    svg_input: SvgInput,
    *,
    densify_distance: float,
    min_branch_length: float,
    simplify: float,
    split_components: bool = True,
    verbose: bool = False,
) -> CenterlineGeometry:
    ...
```

Exact names can vary, but keep the concept: domain input in, Shapely outline and
centerline out.

Implementation guidance:

- Build the filled polygonal shape from `SvgInput.source_paths` rings, using the
  same nested-ring logic currently in `build_shape_from_nested_rings`.
- Reuse existing `compute_centerline`, `compute_single_centerline`, and
  `list_polygon_parts`.
- Keep `run_centerline(parse_args())` behavior for legacy CLI.
- Existing debug SVG helpers may stay in `centerline.py` until `render_svg.py`
  replaces project rendering, but project-facing APIs should not depend on the
  debug renderer.

Defaults for project centerline generation:

- Preserve existing default behavior where possible:
  - `densify_distance=6.0`
  - `min_branch_length=20.0`
  - `simplify=1.0`
  - `split_components=True`
- Later phases can pass these from a small pipeline defaults object if useful.

Tests:

- `tests/test_centerline.py` or equivalent.
- Use a simple rectangle/square domain input from `svg_input.load_svg_input`.
- Assert outline area is positive and centerline is non-empty.
- Assert legacy CLI tests still pass.

## Validate

Run:

```bash
uv run pytest tests/test_centerline.py -v
uv run pytest tests/test_cli.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

