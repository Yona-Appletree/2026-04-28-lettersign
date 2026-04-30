# Milestone 2: Pipeline domain split and normalized centerline SVG - Notes

## Scope of work

Refactor the current centerline script into a typed, project-oriented pipeline
with small modules for SVG input, geometry/domain objects, centerline
generation, marker detection, normalized SVG rendering, and orchestration used
by `lettersign build`.

This milestone should:

- Keep `lettersign build <name>` working from the M1 project CLI.
- Move CLI-independent centerline behavior out of the script-shaped
  `src/lettersign/centerline.py` API.
- Parse SVG input paths and viewBox/size metadata into domain objects.
- Normalize geometry to millimeters for internal/output domain data:
  - use SVG physical unit metadata when available,
  - assume `1 SVG unit = 1 mm` when not available.
- Use lower-left oriented coordinates for downstream geometry.
- Compute the filled shape and centerline using the existing Shapely/pygeoops
  behavior.
- Detect post markers at centerline endpoints and intersections.
- Render generated centerline SVG with:
  - black outlines,
  - no outline fill,
  - red centerlines,
  - green circular posts/markers,
  - no carried-over source styling.
- Add focused tests for unit conversion, domain/path conversion, marker
  detection, SVG rendering structure, and project build integration.
- Keep `README.md` accurate for the implemented M2 behavior.

Out of scope:

- SCAD generation.
- Watch-mode implementation.
- Manual centerline/post edit reconciliation.
- Advanced branch pruning beyond existing centerline options.
- User-editable centerline preservation.

## Current state of the codebase

- `src/lettersign/cli.py` owns the project CLI:
  - `init` creates project directories and config,
  - `build` currently calls the existing centerline renderer directly,
  - `watch` is a stub for M4,
  - non-subcommand invocations delegate to the legacy raw SVG CLI.
- `src/lettersign/config.py` defines `ProjectConfig` with:
  - `height`,
  - `led_channel_width`,
  - `post_height`,
  - `line_resolution`.
- `src/lettersign/project.py` resolves `projects/<name>/` paths.
- `src/lettersign/centerline.py` still contains most algorithmic behavior:
  - argparse for legacy CLI,
  - preset/default application,
  - SVG path flattening via `svgpathtools`,
  - filled-shape construction with Shapely,
  - pygeoops centerline generation,
  - debug SVG rendering,
  - SVG path serialization helpers,
  - small math helpers.
- Existing rendering is still debug-oriented:
  - filled shape is translucent black fill,
  - centerline is pink/red,
  - no endpoint/intersection markers.
- Existing tests cover M1 CLI/config/project behavior, plus a minimal package
  smoke test.
- Example project SVGs live under `projects/Y/` and `projects/fyeah/`.

## Questions that need to be answered

### Confirmation-style questions

| # | Question | Context | Suggested answer |
|---|----------|---------|------------------|
| Q1 | Should `ProjectConfig.line_resolution` drive SVG curve flattening in M2? | Existing legacy CLI has `--flatness` presets; config has `line_resolution = 0.25` mm. | Yes. Use `line_resolution` as the project build flatness/sample spacing; keep legacy CLI presets for raw SVG compatibility. |
| Q2 | Should `led_channel_width` influence the M2 preview centerline stroke width? | M2 does not generate SCAD channels yet, but the preview should start resembling LED routing. | Yes. Render red centerline stroke at `led_channel_width` in SVG units/mm after normalization. |
| Q3 | What radius should green marker circles use in M2? | No marker radius config exists yet. | Use `max(led_channel_width / 2, line_resolution * 2)` for visibility; do not add config until needed. |
| Q4 | Should M2 preserve multi-path identity in domain objects even if centerline still uses the unioned filled shape? | M3 needs per-source-path modules, but M2's centerline algorithm currently unions all filled contours. | Yes. Store source path domains now, compute centerline on the union for v0, and leave per-path centerline partitioning for later if needed. |
| Q5 | Should tests assert exact generated SVG text? | Renderer output will evolve as SVG/SCAD work grows. | No. Prefer structural XML/style assertions and small geometry assertions over full-file goldens. |

Answers:

- Q1: Yes. Use `ProjectConfig.line_resolution` as project build flatness/sample
  spacing. Keep legacy presets for raw SVG compatibility.
- Q2: Yes. Render the red centerline preview stroke using `led_channel_width`
  after normalization.
- Q3: Use a static 5 mm marker radius for now. Make it an easy-to-adjust named
  constant, likely near config/defaults or other pipeline constants, rather than
  adding a user config option yet.
- Q4: Yes. Preserve source path identity in domain objects now, while computing
  the v0 centerline on the unioned filled shape.
- Q5: Yes. Use structural XML/style assertions and small geometry assertions
  instead of broad full-file golden tests.

