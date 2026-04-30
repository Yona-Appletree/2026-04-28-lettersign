# Phase 1: Domain geometry and SVG unit input foundation

## Scope of phase

Create the typed domain layer and SVG input normalization module for M2.

In scope:

- Add `src/lettersign/geometry.py` with small typed dataclasses for the
  pipeline domain.
- Add `src/lettersign/svg_input.py` for SVG metadata parsing, unit scale
  derivation, path flattening, source path identity, and lower-left millimeter
  coordinate conversion.
- Add tests for unit conversion, path/domain conversion, and lower-left
  coordinates.

Out of scope:

- Do not implement marker detection.
- Do not implement the normalized SVG renderer.
- Do not wire `cli.build` to the new pipeline.
- Do not refactor `centerline.py` beyond importing/reusing helper code if
  absolutely necessary.

## Code organization reminders

- Prefer granular files, one concept per file.
- Put dataclasses and public entry points first; helper parsing functions at the
  bottom.
- Keep Shapely out of domain dataclasses where possible. Domain objects should
  be plain typed data.
- Avoid utility-first design. Only add helpers needed for this phase.

## Sub-agent reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- If blocked by unexpected SVG parsing behavior, stop and report.
- Report files changed, validation commands/results, and deviations.

## Implementation details

Read first:

- `AGENTS.md`
- `docs/roadmaps/2026-04-28-lettersign-pipeline/m2-pipeline-domain-normalized-svg/00-notes.md`
- `docs/roadmaps/2026-04-28-lettersign-pipeline/m2-pipeline-domain-normalized-svg/00-design.md`
- `src/lettersign/centerline.py`, especially `flatten_subpath`,
  `estimate_segment_length`, `read_view_box`, and path helpers.

Create `src/lettersign/geometry.py` with dataclasses similar to:

```python
@dataclass(frozen=True)
class Point:
    x: float
    y: float

@dataclass(frozen=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

@dataclass(frozen=True)
class SourcePath:
    name: str
    rings: tuple[tuple[Point, ...], ...]

@dataclass(frozen=True)
class SvgInput:
    path: Path
    view_box: tuple[float, float, float, float]
    unit_scale_mm: float
    bounds: Bounds
    source_paths: tuple[SourcePath, ...]
```

Names can vary if a better local naming pattern emerges, but keep the concepts.
Use tuples for immutable collections.

Create `src/lettersign/svg_input.py` with public functions:

- `load_svg_input(svg_path: Path, *, line_resolution: float) -> SvgInput`
- `parse_length_to_mm(value: str) -> float | None` or equivalent helper for
  unit metadata.
- `derive_unit_scale_mm(root, view_box) -> float` or equivalent.

Unit handling:

- If SVG `width` or `height` has physical units (`mm`, `cm`, `in`, `pt`, `px`)
  and `viewBox` is available, derive SVG unit to mm scale from the physical
  dimension divided by the matching viewBox dimension.
- Supported conversions:
  - `mm`: value
  - `cm`: value * 10
  - `in`: value * 25.4
  - `pt`: value * 25.4 / 72
  - `px`: value * 25.4 / 96
- If no usable metadata exists, return `1.0`.
- If both width and height are usable but slightly differ, prefer width for now
  and leave a small comment in code or test note; do not add config.

Coordinate handling:

- Flatten SVG paths using the same approach as `centerline.flatten_subpath`, with
  sample spacing based on `line_resolution` in SVG units. If `unit_scale_mm` is
  not `1.0`, convert line resolution in mm to SVG units before flattening.
- Convert points to millimeters.
- Convert SVG's y-down viewBox coordinates to lower-left y-up coordinates:
  `x_mm = (x - min_x) * scale`, `y_mm = (height - (y - min_y)) * scale`.
- Preserve source path identity with generated names `path1`, `path2`, etc.

Tests:

- `tests/test_svg_input.py`
- Cover fallback `1 unit = 1 mm`.
- Cover width/viewBox scale, e.g. width `100mm` viewBox width `200` gives
  `0.5 mm/unit`.
- Cover lower-left conversion with a simple square path.
- Cover multiple SVG path elements become `path1`, `path2`.

## Validate

Run:

```bash
uv run pytest tests/test_svg_input.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

