# Milestone 3: SCAD generation foundation - Notes

## Scope of work

Generate readable OpenSCAD output from the project pipeline:

- Write `projects/<name>/<name>_data.scad` on each `lettersign build <name>`.
- Create `projects/<name>/<name>.scad` only if absent, preserving user edits.
- Provide a shared `lettersign_common.scad` helper file for reusable post/common
  modules.
- Generate per-source-path modules:
  - `path1_outline()`,
  - `path1_channel()`,
  - `path1_posts()`,
  - `path1_3d()`.
- Represent outlines from normalized SVG input paths.
- Derive channel polygons by stroking the generated centerline with round caps
  using `led_channel_width` and `line_resolution`.
- Represent posts as simple cylinders using marker positions and `post_height`.
- Keep SCAD human-readable: stable headers, section separators, readable arrays,
  explicit modules, and predictable names.
- Add focused tests for generated module names, wrapper ownership, helper file
  handling, config-driven values, and broad SCAD structure.
- Update `README.md` with implemented SCAD output behavior and generated vs
  user-owned boundaries.

Out of scope:

- Sophisticated post design.
- Manual centerline/post edit reconciliation.
- Print-ready optimization for every SVG edge case.
- Running OpenSCAD in CI or validating meshes.
- Adding new TOML properties unless a design answer explicitly requires one.

## Current state of the codebase

- M1 provides project paths:
  - `ProjectPaths.data_scad` -> `projects/<name>/<name>_data.scad`.
  - `ProjectPaths.wrapper_scad` -> `projects/<name>/<name>.scad`.
- M1 config provides:
  - `height`,
  - `led_channel_width`,
  - `post_height`,
  - `line_resolution`.
- M2 added normalized geometry:
  - `SvgInput.source_paths` preserves original path identity as `path1`,
    `path2`, etc.
  - `SourcePath.rings` are lower-left, millimeter-space points.
  - `generate_centerline_geometry()` computes a unioned outline and centerline,
    not per-source-path centerlines.
  - `detect_markers()` produces global marker positions in millimeter space.
  - `render_centerline_svg()` renders the normalized preview.
  - `pipeline.build_centerline_preview()` currently writes only
    `<name>.centerline.svg`.
- `centerline.geometry_to_svg_path()` already serializes Shapely geometry to SVG
  paths, but there is no SCAD serializer yet.
- `pyproject.toml` currently uses setuptools package discovery, but no package
  data configuration exists for non-Python files such as `.scad` helpers.
- The user's Illustrator exporter example favors:
  - lower-left/center origin options,
  - readable point arrays,
  - explicit `polygon(points=..., paths=...)` modules,
  - slash/comment section separators,
  - grouped top-level module invocations.

## Questions that need to be answered

### Confirmation-style questions

| # | Question | Context | Suggested answer |
|---|----------|---------|------------------|
| Q1 | For M3, should per-path `pathN_channel()` be derived by clipping the global buffered centerline to each source path outline? | M2 computes one union centerline, not per-path centerlines, but M3 wants per-path SCAD modules. | Yes. Keep the v0 centerline global, then clip channel and posts to each source outline for per-path modules. |
| Q2 | Should post cylinder radius use the existing marker radius (`PREVIEW_MARKER_RADIUS_MM = 5.0`) for M3? | Config has `post_height` but no post radius. The milestone says simple cylinders and does not ask for a new config key. | Yes. Use marker radius for cylinder radius; keep radius non-configurable until post design matures. |
| Q3 | Should `lettersign_common.scad` be copied into each project directory during build? | OpenSCAD `use <...>` works best with a relative helper, but copying into every project duplicates shared code. | No. Keep one shared helper at the projects root and reference it from each project. |
| Q4 | Should `<name>_data.scad` use `use <../lettersign_common.scad>` and `<name>.scad` use `use <<name>_data.scad>`? | `use` imports modules/functions without executing top-level statements. The wrapper should invoke modules explicitly. | Yes. Generated data uses the shared projects-root helper; the user wrapper uses generated data and invokes a top-level module. |
| Q5 | Should `pathN_3d()` be a simple printable approximation: extruded outline with an LED channel cut/subtracted and post cylinders added? | M3 is a foundation; print-ready refinements are out of scope. | Yes. Implement readable first-pass geometry using `height`, `led_channel_width`, and `post_height`. |
| Q6 | Should renderer tests remain structural/string-based rather than full golden files? | Roadmap already prefers structural assertions over broad goldens. | Yes. Assert headers, module names, includes, key arrays, and ownership behavior rather than full-file snapshots. |

### Discussion-style questions

No discussion-style questions are currently open. If any confirmation answer
changes the architecture, add follow-up questions here before design.

## Answers

- Q1: Yes. For M3, derive per-path channels by clipping the global buffered
  centerline to each source path outline.
- Q2: Yes. Use the existing 5 mm marker radius for simple post cylinders; do not
  add a post radius config yet.
- Q3: Do not copy the common SCAD helper into every project directory. Keep one
  shared helper at the projects root for now.
- Q4: Yes, with the Q3 path adjustment. Generated data should reference the
  shared helper as `use <../lettersign_common.scad>` from
  `projects/<name>/<name>_data.scad`; the user wrapper should reference
  `<name>_data.scad`.
- Q5: Yes. `pathN_3d()` should be a first-pass extruded outline with the LED
  channel subtracted and post cylinders added.
- Q6: Yes. Keep SCAD tests structural/string-based rather than broad full-file
  goldens.

## Notes

- The channel polygon should be created in Python from Shapely linework via
  `centerline.buffer(led_channel_width / 2, cap_style=round, join_style=round)`.
- `line_resolution` can control Shapely buffer arc resolution by converting it
  into a modest quadrant segment count. The exact mapping can be implementation
  detail as long as it is deterministic and tested.
- Source paths may include multiple rings. SCAD should represent these with one
  points array plus a `paths` index array so holes/compound shapes remain
  expressible by `polygon(points=..., paths=...)`.
