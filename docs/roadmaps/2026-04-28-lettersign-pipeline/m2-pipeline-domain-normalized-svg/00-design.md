# Milestone 2: Pipeline domain split and normalized centerline SVG - Design

## Scope of work

M2 refactors the current centerline script into a project build pipeline with
typed domain objects, SVG input normalization, marker detection, normalized SVG
rendering, and CLI build integration.

The milestone keeps raw SVG legacy behavior working, but `lettersign build
<name>` should use the new project pipeline and produce a normalized
`<name>.centerline.svg`.

## File structure

```text
src/lettersign/
|-- cli.py                  # UPDATE: build calls pipeline instead of centerline namespace
|-- config.py               # UPDATE: preview marker radius constant
|-- geometry.py             # NEW: points, bounds, source paths, preview result objects
|-- svg_input.py            # NEW: SVG metadata, path loading, unit scaling, lower-left conversion
|-- centerline.py           # UPDATE: algorithm helpers; rendering ownership reduced
|-- markers.py              # NEW: endpoint/intersection marker detection
|-- render_svg.py           # NEW: normalized centerline SVG renderer
|-- pipeline.py             # NEW: project build orchestration
`-- errors.py               # UPDATE if needed: SVG/pipeline validation errors

tests/
|-- test_svg_input.py       # NEW
|-- test_geometry.py        # NEW if useful
|-- test_markers.py         # NEW
|-- test_render_svg.py      # NEW
|-- test_pipeline.py        # NEW or equivalent CLI coverage
`-- test_cli.py             # UPDATE: build asserts normalized output
```

## Conceptual architecture

```text
cli.build(name)
    |
    v
pipeline.build_project(paths, config)
    |
    |-- svg_input.load_svg_document(...)
    |       - reads viewBox / width / height
    |       - derives svg-unit -> mm scale
    |       - flattens SVG paths using config.line_resolution
    |       - preserves source path identity
    |       - produces lower-left millimeter coordinates
    |
    |-- centerline.compute_centerline(...)
    |       - still uses Shapely + pygeoops
    |       - computes on unioned filled shape for v0
    |
    |-- markers.detect_markers(...)
    |       - endpoints
    |       - intersections / branch points
    |       - marker radius = PREVIEW_MARKER_RADIUS_MM = 5.0
    |
    `-- render_svg.render_centerline_svg(...)
            - black outline, no fill
            - red centerline, stroke width = config.led_channel_width
            - green circular markers
            - generated-file header/comment
```

## Main components

### Domain geometry

`geometry.py` holds the abstract shapes first: `Point`, optional `Bounds`,
`SourcePath`, `SvgInput`, `Marker`, and a preview/build result object. These
should be typed dataclasses with plain numeric fields. Shapely geometry can
remain an implementation detail of centerline computation and rendering bridge
code where useful.

M2 should preserve source SVG path identity in domain objects even though the
v0 centerline is computed on the unioned filled shape.

### SVG input normalization

`svg_input.py` owns SVG metadata and coordinate normalization:

- Parse `viewBox`, `width`, and `height`.
- Derive SVG-unit-to-mm scale from physical metadata when possible.
- Fall back to `1 SVG unit = 1 mm`.
- Flatten SVG curves using `ProjectConfig.line_resolution`.
- Convert to lower-left oriented millimeter coordinates for domain objects and
  downstream geometry.

### Centerline algorithm

`centerline.py` should become algorithm-heavy rather than app-heavy. The
existing raw SVG CLI can remain as compatibility, but project rendering should
move to `pipeline.py` + `render_svg.py`.

The pygeoops/Shapely centerline behavior should stay conservative: preserve
existing default pruning/simplification behavior unless a phase explicitly needs
to adapt it for the project config.

### Marker detection

`markers.py` operates on line geometry and returns marker domain objects.

For M2:

- place markers at centerline endpoints,
- place markers at intersections / branch points,
- deduplicate nearby marker points using a small tolerance,
- use a named static radius constant `PREVIEW_MARKER_RADIUS_MM = 5.0` rather
  than adding user config.

### Normalized SVG rendering

`render_svg.py` owns output style and should not carry over source SVG styling.
It renders:

- original outlines as black stroke and no fill,
- centerlines in red with stroke width `config.led_channel_width`,
- markers as green circles with radius `PREVIEW_MARKER_RADIUS_MM`.

Tests should use structural XML and style assertions, not broad full-file
goldens.

### Pipeline orchestration

`pipeline.py` is the narrow orchestration layer used by `cli.cmd_build`:

1. Load and normalize SVG input.
2. Build the unioned filled shape.
3. Compute centerline.
4. Detect markers.
5. Render normalized SVG.
6. Write `paths.centerline_svg`.

## Main risks

- `centerline.py` is currently doing many jobs. Refactoring should avoid a
  risky big-bang rewrite; phases should migrate responsibilities gradually.
- SVG physical unit metadata can be inconsistent. Tests should cover common
  metadata cases and the fallback.
- Marker detection needs to be good enough for obvious endpoints/branches, but
  not perfect CAD topology.
- Generated SVG output should be readable and stable, but tests should avoid
  over-specifying whitespace and path formatting.

