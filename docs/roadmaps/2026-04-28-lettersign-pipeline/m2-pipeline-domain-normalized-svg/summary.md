### What was built

- Typed domain layer (`geometry.py`): points, bounds, source paths, SVG input envelope, markers.
- SVG ingestion (`svg_input.py`): viewBox and physical width/height metadata for mm scaling, lower-left normalization, curve flattening driven by `ProjectConfig.line_resolution`.
- Centerline computation (`centerline.py`): `SvgInput` to unioned outline plus pygeoops centerline; legacy raw-SVG CLI unchanged (debug SVG, presets).
- Marker detection (`markers.py`): endpoints and branch/intersection points with deduplication.
- Normalized preview renderer (`render_svg.py`): black outline (no fill), red centerline stroke width from `led_channel_width`, green marker circles, generated-file comment, and no inherited source styling.
- Pipeline orchestration (`pipeline.py`): wires load to centerline to markers to render to `<name>.centerline.svg`; maps SVG failures to `InvalidSvgInputError`.
- CLI (`cli.py`): `build` uses the pipeline; non-subcommand argv still delegates to legacy centerline with presets.
- Tests: unit coverage for svg input, markers, renderer structure, pipeline, centerline-from-SvgInput, CLI build + legacy paths; renderer/pipeline tests use XML/shape assertions, not full-file goldens.

### Decisions for future reference

#### Preview marker radius

The green preview marker circles use a fixed **5 mm** radius exposed as `PREVIEW_MARKER_RADIUS_MM` in `config.py`. It is intentionally **not** user-configurable in TOML until product needs justify it.

#### Flattening: project build vs legacy CLI

Project **`lettersign build`** flattens Bezier curves using **`line_resolution`** from the project TOML (mm-space sampling via svg-unit flatness derived after scaling).

The **legacy** raw-SVG invocation keeps **`--preset`** / **`--flatness`** semantics unchanged for compatibility.

#### SVG regression testing

Generated SVG is exercised with **structural** checks (elements, attributes, key styles, numeric spots like stroke width and marker radius) rather than brittle **full-file golden** snapshots, so formatter/path-detail churn does not break tests unnecessarily.
