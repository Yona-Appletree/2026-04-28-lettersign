# Phase 2: SCAD geometry model and clipping

## Scope of phase

Build the typed geometry conversion layer used by SCAD rendering.

In scope:

- Add `src/lettersign/scad_geometry.py`.
- Convert `SvgInput.source_paths`, centerline geometry, markers, and
  `ProjectConfig` into a SCAD-friendly model.
- Build per-path outline polygon data from source path rings.
- Derive per-path channel polygons by buffering the global centerline and
  clipping to each source path outline.
- Filter posts per path by containment/intersection with that source outline.
- Add tests for clipping, module/path names, and config-derived dimensions.

Out of scope:

- Do not render SCAD text.
- Do not write files.
- Do not wire pipeline/CLI.
- Do not add new TOML keys.
- Do not implement sophisticated post design or manual reconciliation.

## Code Organization Reminders

- Keep Shapely-specific details inside this conversion module.
- Prefer typed dataclasses for the SCAD model.
- Put public dataclasses/functions first; helper conversion functions lower.
- Keep related geometry transformations grouped together.
- Temporary code must have a TODO comment so cleanup can find it.

## Sub-agent Reminders

- Do not commit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- If Shapely geometry conversion becomes ambiguous, keep the simplest
  deterministic implementation and report limitations.
- Report files changed, validation commands/results, and deviations.

## Implementation Details

Read:

- `src/lettersign/geometry.py`
- `src/lettersign/centerline.py`
- `src/lettersign/markers.py`
- `src/lettersign/config.py`
- M3 `00-notes.md` and `00-design.md`

Create `src/lettersign/scad_geometry.py`.

Suggested public dataclasses:

```python
@dataclass(frozen=True)
class ScadPolygon:
    points: tuple[Point, ...]
    paths: tuple[tuple[int, ...], ...]

@dataclass(frozen=True)
class ScadPost:
    position: Point
    radius_mm: float
    height_mm: float

@dataclass(frozen=True)
class ScadPathPart:
    name: str
    outline: ScadPolygon
    channels: tuple[ScadPolygon, ...]
    posts: tuple[ScadPost, ...]

@dataclass(frozen=True)
class ScadModel:
    project_name: str
    height_mm: float
    led_channel_width_mm: float
    post_height_mm: float
    parts: tuple[ScadPathPart, ...]
```

Names can vary if clearer, but preserve the concepts.

Create a public function like:

```python
def build_scad_model(
    *,
    project_name: str,
    svg_input: SvgInput,
    outline: Polygon | MultiPolygon,
    centerline: BaseGeometry,
    markers: Sequence[Marker],
    config: ProjectConfig,
) -> ScadModel:
    ...
```

Behavior:

- For each `SourcePath`, build a Shapely polygon/multipolygon from its rings.
  Reuse or mirror the nested-ring logic in `centerline.build_shape_from_nested_rings`.
- Preserve source names (`path1`, `path2`, etc.).
- Convert source outline rings into `ScadPolygon` with one flat points tuple and
  `paths` index tuples. This keeps compound paths/holes expressible as
  `polygon(points=..., paths=...)`.
- Create a global channel shape:
  - `centerline.buffer(config.led_channel_width / 2, cap_style=round,
    join_style=round, resolution=...)`.
  - Use deterministic resolution derived from `line_resolution`; a simple
    helper such as `max(4, min(32, ceil((led_channel_width / 2) / line_resolution)))`
    is acceptable.
- Intersect the global channel shape with each source outline shape.
- Convert channel polygons from the clipped result into zero or more
  `ScadPolygon`s.
- For posts, keep markers whose point is contained by or intersects/touches the
  source outline. Use marker radius and `config.post_height`.
- Empty channel intersections should produce `channels=()`, not a crash.

Tests:

- Add `tests/test_scad_geometry.py`.
- Use small Shapely rectangles/lines or load a simple SVG and centerline result.
- Assert:
  - one source path yields one `ScadPathPart` named `path1`,
  - outline points/paths are populated,
  - a centerline inside the source outline produces at least one channel,
  - a marker inside the outline becomes a `ScadPost`,
  - a marker outside the outline is excluded,
  - post height and channel width come from `ProjectConfig`.

## Validate

Run:

```bash
uv run pytest tests/test_scad_geometry.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

