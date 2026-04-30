# Phase 4: Normalized SVG renderer

## Scope of phase

Implement normalized centerline SVG rendering independent of the legacy debug
renderer.

In scope:

- Add `src/lettersign/render_svg.py`.
- Render black no-fill outlines, red centerlines, and green circular markers.
- Use `ProjectConfig.led_channel_width` for the centerline stroke width.
- Use the static `PREVIEW_MARKER_RADIUS_MM = 5.0` marker radius via marker
  domain objects.
- Add structural XML/style tests.

Out of scope:

- Do not detect markers.
- Do not wire `cli.build`.
- Do not generate SCAD.
- Do not preserve or copy source SVG styling.

## Code organization reminders

- Renderer public API first; serialization helpers lower in the file.
- Keep formatting readable and deterministic.
- Prefer structural tests over full-file goldens.

## Sub-agent reminders

- Do not commit.
- Do not expand scope.
- Do not weaken tests.
- If domain objects from Phase 1/3 are missing expected fields, stop and report
  rather than changing unrelated phases broadly.
- Report files changed, validation commands/results, and deviations.

## Implementation details

Read:

- `src/lettersign/geometry.py`
- `src/lettersign/config.py`
- `src/lettersign/centerline.py` path serialization helpers
- M2 `00-design.md`

Create `src/lettersign/render_svg.py` with a public API like:

```python
def render_centerline_svg(
    *,
    view_box: tuple[float, float, float, float],
    outlines: BaseGeometry,
    centerline: BaseGeometry,
    markers: Sequence[Marker],
    led_channel_width: float,
) -> str:
    ...
```

Exact parameter names can vary; keep the renderer free of filesystem writes.

Rendering requirements:

- XML declaration.
- `<svg xmlns="http://www.w3.org/2000/svg" viewBox="...">`.
- Optional generated comment/header.
- Outline path:
  - `fill="none"`
  - `stroke="black"` or `#000000`
  - no source style attributes.
- Centerline path:
  - `fill="none"`
  - `stroke="red"` or a stable red hex.
  - `stroke-width` from `led_channel_width`.
  - round line caps/joins.
- Marker circles:
  - green fill/stroke.
  - `r` from marker radius.

Coordinate note:

- Domain geometry is lower-left y-up millimeter geometry. For the generated SVG,
  it is acceptable in M2 to use a lower-left-y-up viewBox by setting viewBox to
  normalized mm bounds and rendering those coordinates directly. Do not attempt
  to preserve the original SVG coordinate orientation.

Tests:

- `tests/test_render_svg.py`.
- Parse output with `xml.etree.ElementTree`.
- Assert there is an outline path with fill none and black stroke.
- Assert centerline path has red stroke and stroke-width matching config.
- Assert marker circles are green and have radius `5`.
- Assert source styles are not present in renderer output.

## Validate

Run:

```bash
uv run pytest tests/test_render_svg.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

