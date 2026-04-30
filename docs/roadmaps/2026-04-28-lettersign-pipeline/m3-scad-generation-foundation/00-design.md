# Milestone 3: SCAD generation foundation - Design

## Scope of work

M3 adds the first OpenSCAD generation path to the project build pipeline.
`lettersign build <name>` should continue writing the normalized centerline SVG,
and should also:

- write generated SCAD data to `projects/<name>/<name>_data.scad`,
- create `projects/<name>/<name>.scad` only if missing,
- write/update one shared helper at `projects/lettersign_common.scad`,
- generate readable per-source-path modules:
  - `path1_outline()`,
  - `path1_channel()`,
  - `path1_posts()`,
  - `path1_3d()`.

The generated data file is owned by the tool and overwritten. The wrapper is
user-owned and must not be overwritten once it exists.

Out of scope:

- Sophisticated post design.
- Manual centerline/post edit reconciliation.
- OpenSCAD rendering or mesh validation in CI.
- Print-ready optimization for every SVG edge case.
- New user config keys.

## File structure

```text
src/lettersign/
|-- project.py              # UPDATE: projects-root shared SCAD helper path
|-- pipeline.py             # UPDATE: build writes SVG + SCAD outputs
|-- geometry.py             # UPDATE: add SCAD-ready domain objects if useful
|-- scad_geometry.py        # NEW: source paths/centerlines/markers to SCAD shapes
|-- render_scad.py          # NEW: render data SCAD, wrapper, shared helper
|-- scad/
|   `-- lettersign_common.scad  # NEW: canonical helper copied to projects root
`-- errors.py               # UPDATE if SCAD-specific user errors are needed

tests/
|-- test_scad_geometry.py   # NEW
|-- test_render_scad.py     # NEW
|-- test_pipeline.py        # UPDATE: build writes SCAD files too
`-- test_cli.py             # UPDATE: CLI integration checks SCAD outputs
```

Generated project layout:

```text
projects/
|-- lettersign_common.scad      # shared helper, generated/updated by build
`-- <name>/
    |-- <name>.svg              # user-authored input artwork
    |-- <name>.toml             # user config
    |-- <name>.centerline.svg   # generated normalized preview
    |-- <name>_data.scad        # generated/overwritten
    `-- <name>.scad             # user-owned wrapper, create only if absent
```

## Conceptual architecture

```text
lettersign build <name>
    |
    v
load config + normalized SVG input
    |
    v
compute union outline + centerline + markers
    |
    |-- render_svg.render_centerline_svg(...)
    |       -> projects/<name>/<name>.centerline.svg
    |
    `-- scad_geometry.build_scad_model(...)
            |
            |-- source path outline polygons
            |-- global centerline buffer clipped per source path
            `-- markers filtered/clipped per source path
                    |
                    v
              render_scad.write_scad_outputs(...)
                    |
                    |-- projects/lettersign_common.scad
                    |-- projects/<name>/<name>_data.scad
                    `-- projects/<name>/<name>.scad (only if absent)
```

## Main components

### Project paths

`ProjectPaths` should grow a `common_scad` path for the shared helper:

```python
common_scad = projects_root / "lettersign_common.scad"
```

This keeps one shared helper in the project root, rather than copying the helper
into each project directory.

### SCAD geometry model

`scad_geometry.py` converts existing M2 domain/algorithm output into a
SCAD-friendly model. It should keep Shapely details inside the conversion layer
and expose small typed dataclasses such as:

- a per-path SCAD part,
- outline polygon data,
- channel polygon data,
- post marker positions,
- a whole SCAD model.

For M3, centerlines remain global. Per-path `pathN_channel()` is derived by
buffering the global centerline with round caps/joins and clipping that buffer
to each source path outline.

Post markers are filtered per source path by intersection/containment with that
source outline. Post cylinders use the existing 5 mm marker radius and
`ProjectConfig.post_height`.

### SCAD rendering

`render_scad.py` owns text rendering and filesystem write policies:

- data SCAD is generated and overwritten,
- wrapper SCAD is created only if absent,
- common helper at `projects/lettersign_common.scad` is generated/updated.

Generated data should use the shared helper with:

```scad
use <../lettersign_common.scad>
```

The wrapper should use the project data file with:

```scad
use <<name>_data.scad>
```

The SCAD should favor readability over compactness: stable generated-file
headers, section separators, explicit arrays, named modules, and predictable
formatting.

### Module shape

For each source path:

- `pathN_outline()` emits `polygon(points=..., paths=...)`.
- `pathN_channel()` emits one or more channel polygons derived from the buffered
  centerline.
- `pathN_posts()` places simple helper cylinders at marker positions.
- `pathN_3d()` is a first-pass printable approximation:
  - extrude the outline by `height`,
  - subtract the LED channel shape,
  - add post cylinders using `post_height`.

The generated file should also include a top-level module such as
`<name>_3d()` that invokes every `pathN_3d()`. The user wrapper can call this
top-level module by default.

### Testing approach

Tests should be structural rather than broad full-file goldens:

- module names exist,
- `use` paths are correct,
- generated headers identify generated/user-owned files,
- wrapper preservation works,
- config values appear in the right places,
- SCAD array/path structure is present,
- pipeline/CLI write expected SCAD files.

