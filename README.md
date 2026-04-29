# lettersign

Build **3D-printable letters** that conceal **side-emitting addressable LED strip**, then mount the assembly on a **backing board** to form a lit sign.

This repository holds **lettersign** — small tooling that turns outline SVG artwork into experiments for routing LED channels (approximate centerlines through filled shapes). Output is aimed at layout and iteration, not a turnkey CAD pipeline.

## CLI

Install dependencies and run from the repo root:

```bash
uv sync --group dev
uv run lettersign path/to/letter.svg
uv run lettersign path/to/letter.svg --preset fast -o debug.svg
```

The tool writes a debug SVG overlaying the filled shape and a computed centerline trace.
