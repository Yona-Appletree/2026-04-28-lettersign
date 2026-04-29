# lettersign

Build **3D-printable letters** that conceal **side-emitting addressable LED strip**, then mount the assembly on a **backing board** to form a lit sign.

This repository holds **lettersign** - small tooling for turning outline SVG artwork into LED-channel centerlines and, over time, OpenSCAD geometry for printable sign letters. Output is aimed at layout and iteration: edit the SVG, regenerate previews/data, inspect the result, and customize the final SCAD wrapper as needed.

## Current CLI

Install dependencies and run from the repo root:

```bash
uv sync --group dev
uv run lettersign path/to/letter.svg
uv run lettersign path/to/letter.svg --preset fast -o debug.svg
```

The tool writes a debug SVG overlaying the filled shape and a computed centerline trace.

## Planned Project Workflow

Projects live under `projects/<name>/`:

```text
projects/<name>/
|-- <name>.svg             # user-authored input artwork
|-- <name>.toml            # project config
|-- <name>.centerline.svg  # generated preview: black outline, red centerline, green posts
|-- <name>_data.scad       # generated OpenSCAD data/modules
`-- <name>.scad            # user-owned wrapper, created once and not overwritten
```

Planned commands:

```bash
uv run lettersign init <name>
uv run lettersign build <name>
uv run lettersign watch <name>
```

Initial config defaults:

- `height = 15` mm
- `led_channel_width = 3` mm
- `post_height = 12` mm
- `line_resolution = 0.25` mm

The generated SCAD will use modules per source SVG path, such as
`path1_outline`, `path1_channel`, `path1_posts`, and `path1_3d()`, plus shared
helpers for common geometry like posts.

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
