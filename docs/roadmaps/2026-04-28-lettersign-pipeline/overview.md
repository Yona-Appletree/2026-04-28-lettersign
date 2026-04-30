# lettersign Pipeline Roadmap

## Motivation / rationale

`lettersign` should become a small but solid pipeline for making illuminated,
3D-printable sign letters: user-authored SVG outlines go in, normalized
centerline previews and OpenSCAD geometry come out. The project needs to support
an iterative workflow where the user can edit artwork, rerun or watch, inspect
the generated centerline/posts, and eventually produce SCAD for printable letter
bodies with LED channels and mounting posts.

The current code proves the hard first experiment: converting a filled SVG path
into a centerline. The pain now is structure. The CLI still thinks in raw SVG
files, all logic sits in one module, there is no project config, no SCAD output,
and no testable domain boundary for the pipeline as it grows.

## Architecture / design

The roadmap moves from one script-shaped module to a project pipeline:

```text
src/lettersign/
|-- cli.py                 # parse commands: init/build/watch
|-- project.py             # project names, paths, generated/user-owned files
|-- config.py              # ProjectConfig + tomlkit read/update/write
|-- svg_input.py           # read SVG paths, metadata, unit scale
|-- geometry.py            # domain objects: paths, outlines, centerlines, markers
|-- centerline.py          # centerline algorithm, no CLI ownership
|-- markers.py             # endpoints/intersections/post marker detection
|-- render_svg.py          # normalized centerline SVG renderer
|-- render_scad.py         # <name>_data.scad and wrapper generation
|-- scad/
|   `-- lettersign_common.scad
`-- errors.py              # user-facing validation/errors
```

Project flow:

```text
projects/<name>/<name>.svg
        |
        v
ProjectConfig from <name>.toml
        |
        v
SVG path parsing + unit normalization
        |
        v
outline paths + derived centerlines + post markers
        |
        |-- <name>.centerline.svg
        |       black outlines, red centerlines, green posts
        |
        `-- <name>_data.scad
                path1_outline()
                path1_channel()
                path1_posts()
                path1_3d()
```

Generated/user-owned boundary:

- `<name>.svg`: user-authored input.
- `<name>.toml`: user-owned but schema-managed with missing defaults added.
- `<name>.centerline.svg`: generated in v0; future manual-edit reconciliation
  deferred.
- `<name>_data.scad`: generated and overwritten.
- `<name>.scad`: user-owned wrapper, created only if absent.
- `lettersign_common.scad`: shared helpers for posts and common generated
  modules.

SCAD generation should follow the style in the user's existing OpenSCAD work:
readable arrays, explicit modules, clear section separators, stable helper
files, and a user-editable top-level wrapper.

## Alternatives considered

- **Keep a raw SVG-path CLI** - rejected because the target workflow is
  project-based and needs config, generated files, and watch mode.
- **Generate only centerline SVG first** - rejected as too small; the roadmap
  should reach initial SCAD output, even if post/channel geometry starts simple.
- **Overwrite all generated-looking files** - rejected because `<name>.scad` is
  meant to be a customization layer. Generated data and user-owned wrappers need
  different rules.
- **Use stdlib `tomllib` only** - rejected because it cannot write TOML or
  preserve user comments/formatting.
- **Full-file golden tests everywhere** - rejected because SVG/SCAD formatting
  will evolve; structural tests will be more useful early.

## Risks

- SVG unit metadata may be incomplete or inconsistent; defaulting to
  `1 unit = 1 mm` is sane but needs visible config override later.
- Centerline generation can create unattractive branches near edges; v0 assumes
  no manual trimming, but the roadmap should preserve a later reconciliation
  design.
- Watch mode can become flaky in CI if tested too aggressively; keep its
  automated test small.
- OpenSCAD output needs to be readable enough for human customization while
  still machine-generated enough to update reliably.
- Splitting the current module too eagerly could add ceremony; milestones should
  refactor only as needed to make the pipeline testable.

## Scope estimate

Six milestones:

| # | Milestone | Strategy |
|---|-----------|----------|
| M5 | AGENTS.md, docs, and style guidance | Direct |
| M1 | Project/config/CLI foundation | Small plan |
| M2 | Pipeline domain split and normalized centerline SVG | Full plan |
| M3 | SCAD generation foundation | Full plan |
| M4 | Watch mode and generated/user-owned file safety | Small plan |
| M6 | Integration validation and cleanup | Small plan |

M5 is listed first intentionally: the guidance should exist before the larger
implementation milestones so future agents inherit the desired project style.

