# lettersign

Build **3D-printable letters** that conceal **side-emitting addressable LED strip**, then mount the assembly on a **backing board** to form a lit sign.

This repository holds **lettersign** - tooling for turning outline SVG artwork into LED-channel centerlines and OpenSCAD geometry for printable sign letters. Output is aimed at layout and iteration: edit the SVG, regenerate previews and generated data, inspect the result, and customize the SCAD wrapper as needed.

## Project CLI

Projects live under `projects/<name>/` by default. You can point elsewhere with `-p` / `--projects-root` before the subcommand:

```bash
uv sync --group dev
uv run lettersign init myletter
uv run lettersign build myletter
uv run lettersign watch myletter
```

Examples with a custom projects root:

```bash
uv run lettersign -p /path/to/projects init demo
uv run lettersign --projects-root /path/to/projects build demo
```

### Commands

- **`init <name>`** - Creates `projects/<name>/` if needed, creates or updates `<name>.toml` with defaults (preserving existing values and comments), and prints the expected input SVG path if `<name>.svg` is not present yet.
- **`build <name>`** - Resolves paths, loads or creates the config, requires `<name>.svg`, and runs the project pipeline: normalize SVG geometry to millimeters (using physical SVG units when present, otherwise `1` SVG unit = `1` mm), compute the LED centerline and post markers, then write outputs described below (centerline preview, OpenSCAD data, and shared helper). The SVG preview uses a fixed style; it does **not** copy fills or strokes from the source SVG.
- **`watch <name>`** - Resolves the project and config only. A real file-watch loop is **not** implemented yet; the command prints that automatic rebuilds are planned for milestone 4 (M4).

### Centerline preview (`<name>.centerline.svg`)

After `lettersign build <name>`, the generated file is a **normalized** preview intended for layout and mounting planning:

- **Outlines** - black stroke, no fill (input paths in lower-left mm space).
- **Centerline** - red stroke; stroke width follows `led_channel_width` from `<name>.toml`.
- **Post markers** - green circles with **5 mm** radius at centerline endpoints and branch/intersection points.

### OpenSCAD output (`build`)

`lettersign build <name>` also writes OpenSCAD for a first-pass printable letter model:

- **`projects/<name>/<name>.centerline.svg`** - normalized preview (regenerated every build).
- **`projects/<name>/<name>_data.scad`** - generated geometry data (regenerated every build). Includes `use <../lettersign_common.scad>` for shared post helpers.
- **`projects/lettersign_common.scad`** - shared helper at the projects root (written/updated every build). One copy for all projects under that root.
- **`projects/<name>/<name>.scad`** - user-editable wrapper: **created only if the file is missing**. Later builds do not overwrite it.

**Generated vs user-owned**

- **Regenerated on each `build`**: `<name>.centerline.svg`, `<name>_data.scad`, and `projects/lettersign_common.scad`.
- **User-owned / preserved**: `<name>.svg`; `<name>.toml` (the tool merges defaults but keeps existing values and comments); `<name>.scad` once that wrapper file exists (later builds never overwrite it).

For each source path in the SVG (`path1`, `path2`, ...), the data file defines modules:

- **`pathN_outline()`** - `polygon(points=..., paths=...)` for the normalized outline.
- **`pathN_channel()`** - LED channel region derived from the **global** centerline stroked with round caps (`led_channel_width`, `line_resolution`), then **clipped** to that path's outline.
- **`pathN_posts()`** - simple **cylinders** at markers associated with the path (same **5 mm** radius as preview markers; height from `post_height`).
- **`pathN_3d()`** - first-pass solid: extruded outline, channel subtracted, posts unioned. This is a foundation for iteration, not a guarantee of print-ready geometry for every SVG.

The data file also defines a top-level assembler module named from the project directory (sanitized for OpenSCAD identifiers), for example **`myletter_3d()`** for project `myletter`. The default wrapper calls that module after `use <<name>_data.scad>`.

**M3 limitations (current milestone)** - Posts are basic cylinders; the channel is the clipped buffered centerline, not a fully tuned manufacturing workflow. Refinements and manual reconciliation of centerlines or posts are **future** work, not implemented here.

### Config defaults (`<name>.toml`)

The tool merges defaults into an existing file and preserves user edits where practical:

- `height = 15` mm
- `led_channel_width = 3` mm
- `post_height = 12` mm
- `line_resolution = 0.25` mm - sample spacing / flatness when flattening curves from the input SVG during `build`.

`build` uses `line_resolution` and `led_channel_width` for SVG flattening, centerline stroke width in the preview, and channel geometry in SCAD. `height` controls extrusion depth in `pathN_3d()`; `post_height` sets cylinder height for posts in SCAD (markers in the SVG preview remain schematic).

### Project layout

```text
projects/
|-- lettersign_common.scad # shared OpenSCAD helper (generated/updated by `build`)
`-- <name>/
    |-- <name>.svg             # user-authored input artwork (required for build)
    |-- <name>.toml            # project config (created/updated by the tool)
    |-- <name>.centerline.svg  # generated preview (`build`)
    |-- <name>_data.scad       # generated OpenSCAD data (`build`)
    `-- <name>.scad            # user wrapper: created on first `build` if missing, then preserved
```

## Legacy: raw SVG invocation

For compatibility, if the first argument is **not** a project subcommand (`init`, `build`, or `watch`), the CLI delegates to the **legacy** centerline entry point (debug-oriented styling and presets), not the normalized project preview:

```bash
uv run lettersign path/to/letter.svg
uv run lettersign path/to/letter.svg --preset fast -o debug.svg
```

## Development

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

See [`AGENTS.md`](AGENTS.md) for project coding conventions and
[`docs/roadmaps/2026-04-28-lettersign-pipeline/`](docs/roadmaps/2026-04-28-lettersign-pipeline/)
for the current roadmap.

## License

Released under the [MIT License](LICENSE).
