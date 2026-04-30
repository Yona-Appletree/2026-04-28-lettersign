# lettersign Pipeline Roadmap - Notes

## Scope of the effort

Build `lettersign` from a single centerline SVG experiment into a small, clean,
project-oriented pipeline for illuminated 3D-printable signs.

The effort covers:

- Project layout conventions:
  - projects live in `projects/<name>/`,
  - user-authored input SVG is `projects/<name>/<name>.svg`,
  - project config is `projects/<name>/<name>.toml`.
- A CLI that takes a project name, resolves project paths, creates missing
  config with defaults, and updates existing config files when new properties
  are introduced.
- Watch mode so a user can run the CLI once, edit the source SVG, and have
  generated artifacts refreshed automatically.
- A normalized centerline SVG output:
  - original outlines normalized to black stroke and no fill,
  - centerline rendered red,
  - endpoints and intersections rendered as green circular post markers,
  - unnecessary source SVG styling stripped from generated output.
- Domain objects and small, single-purpose modules for config, projects, SVG
  parsing, centerline generation, marker detection, SVG rendering, SCAD data
  generation, and CLI orchestration.
- OpenSCAD generation:
  - a shared/common SCAD file for reusable helpers such as posts,
  - generated per-project `<name>_data.scad`,
  - user-owned `<name>.scad` wrapper created only if absent,
  - per-SVG-path modules such as `path1_outline`, `path1_channel`,
    `path1_posts`, and `path1_3d()`.
- A configuration model with initial properties:
  - `height = 15` mm,
  - `led_channel_width = 3` mm,
  - `post_height = 12` mm,
  - `line_resolution = 0.25` mm.
- Error checking, typed code, clean organization, and tests as first-class
  deliverables.
- `AGENTS.md` guidance encoding project style preferences:
  - type-focused code,
  - small single-purpose files,
  - most abstract/domain-level concepts first, then utilities.

Out of scope for the first roadmap pass:

- Manual centerline editing and trim/reconcile workflow. For now, assume the
  generated centerline flows directly into SCAD.
- Sophisticated post geometry. Posts are initially cylinders, with a clean
  module boundary so they can be improved later.
- Full CAD correctness for every complex SVG. The v0 target is reliable
  structure, good diagnostics, and useful output for the current project shapes.

## Current state of the codebase

- The package is named `lettersign` and uses a `src/lettersign` layout.
- `pyproject.toml` exposes a `lettersign` console script pointing at
  `lettersign.centerline:main`.
- `src/lettersign/centerline.py` currently owns CLI parsing, SVG loading,
  curve flattening, Shapely polygon construction, pygeoops centerline
  generation, and debug SVG rendering in one file.
- `projects/` already exists with example project assets such as:
  - `projects/Y/Y.svg`,
  - `projects/Y/Y.centerline.svg`,
  - `projects/fyeah/fyeah.svg`,
  - `projects/fyeah/fyeah.centerline.svg`.
- There is no TOML project config, project resolver, watch mode, SCAD output,
  shared SCAD library, marker detection, or `AGENTS.md` yet.
- Tests currently include only a minimal package-version smoke test.
- Ruff, pytest, uv, GitHub CI, README, and MIT license are already set up.
- Existing Illustrator JSX reference:
  `/Users/yona/Dropbox/maker-projects/illustrator_scripts/paths_to_scad3.jsx`
  demonstrates useful SCAD export conventions:
  - converting path coordinates to millimeters,
  - preserving path/group structure,
  - writing point arrays and path arrays,
  - generating OpenSCAD polygon modules,
  - using bounds/centers metadata,
  - normalizing origin behavior.
- Existing OpenSCAD style references in
  `/Users/yona/Dropbox/maker-projects/RaquelDandelion` show preferences worth
  carrying into generated/user-facing SCAD:
  - top-level scene/invocation section using `*`-disabled sample invocations,
  - explicit section separators and short comments,
  - module-first organization for scenes and parts,
  - shared helper files included from a concise top-level `.scad`,
  - array constants and index constants for generated geometry data,
  - readable generated point/path arrays rather than opaque binary artifacts.

## Questions that need to be answered

### Q1: What should the first OpenSCAD output target be?

Context: The existing tool can generate centerlines, but no CAD yet. The user
clarified that v0 should generate structured SCAD, not merely import/extrude
source art.

Suggested answer: Generate procedural SCAD data from SVG paths and derived
centerline channels. Put generated modules in `<name>_data.scad`, create
user-owned `<name>.scad` only if absent, and put shared helpers in a common
SCAD file.

Answer: Use the procedural SCAD data approach. Config includes `height`,
`led_channel_width`, `post_height`, and `line_resolution`. For each original SVG
path, generate modules like `path1_outline`, `path1_channel`, `path1_posts`,
and `path1_3d()`.

### Q2: How should units and coordinate origin be handled?

Context: Existing SVG/project files may use Illustrator-style SVG coordinates,
while OpenSCAD output should be in millimeters. The Illustrator JSX reference
uses `coordToMm(coord) = round(coord / .02834645) / 100` and supports origin
modes such as center and lower-left.

Suggested answer: Make millimeters the internal domain/output unit. Derive SVG
unit conversion from the SVG metadata when possible, provide an explicit config
override when needed, and use a stable default origin suitable for OpenSCAD
editing.

Answer: Use millimeters as the internal/output unit. If SVG metadata provides a
physical unit scale, use it. If no scale metadata is available, assume
`1 SVG unit = 1 mm`. Use a lower-left oriented coordinate space by default for
OpenSCAD output.

### Q3: What should the first CLI surface look like?

Context: The current CLI takes an SVG path. The desired CLI should take a
project name and be "smart" about creating config and refreshing generated
outputs. Watch mode should let the user edit SVG freely while the pipeline
reruns.

Suggested answer: Start with `lettersign <project-name>` as the main command,
with options such as `--watch`, `--once`, `--verbose`, and maybe `--force`.
Default behavior can be one-shot generation first, with watch mode explicit
until the pipeline is stable.

Answer: Use a simple command-first CLI:

- `lettersign init <name>` creates project/config/wrapper scaffolding.
- `lettersign build <name>` runs the pipeline once.
- `lettersign watch <name>` watches inputs and rebuilds.
- `lettersign <name>` can become an alias for `build <name>` once the CLI is
  mature.

### Q4: How should generated files and user-owned files be protected?

Context: `<name>_data.scad` is generated and should be overwritten. `<name>.scad`
is user-owned and should be created only if missing. Centerline SVG may
eventually become user-editable, but v0 assumes no manual editing.

Suggested answer: Treat `<name>_data.scad` and generated centerline SVG as
regenerable outputs with headers. Treat `<name>.scad` and `<name>.toml` as
user-owned files, only adding missing config keys and never replacing existing
values or comments unless a TOML-preserving library is selected.

Answer: For v0, treat `*.centerline.svg` and `*_data.scad` as generated outputs
that may be overwritten, with clear generated-file headers. Treat `<name>.scad`
as user-owned: create only if missing, never overwrite. Treat `<name>.toml` as
user-owned but schema-managed: preserve existing values and add missing defaults
when new config keys appear. Shared SCAD helpers should be stable project/package
files, not rewritten every build unless their version changes.

Deferred manual-edit reconciliation: Later versions should support user edits to
posts and centerline paths. Likely edits include moving/deleting/creating posts
and deleting unattractive centerline segments. One candidate strategy is to keep
user-approved geometry in bright colors, render newly generated/reintroduced
geometry in desaturated colors, and let the user accept generated changes by
changing the color. For example, accepted posts are bright green; regenerated
candidate posts are darker/desaturated green. The same pattern may apply to
centerline segments.

### Q5: Which TOML library should preserve config edits and comments?

Context: The stdlib has `tomllib` for reading TOML in Python 3.11+, but it does
not write TOML or preserve comments/formatting. The roadmap needs config
round-tripping so new properties can be added visibly without clobbering user
edits.

Suggested answer: Add `tomlkit` for comment-preserving TOML read/write. Keep a
typed `ProjectConfig` domain object separate from the `tomlkit` document layer.

Answer: Use `tomlkit` for comment-preserving TOML read/write. Keep a typed
`ProjectConfig` domain object separate from the TOML document/update layer.

### Q6: What is the v0 testing strategy?

Context: The user values error checking, good domain objects, clean code, and
tests even in a small project. The current test suite is only a smoke test.

Suggested answer: Build tests around pure domain/config/path-rendering units
first, then add fixture-based integration tests using tiny SVG projects and
golden-ish assertions for generated file structure rather than brittle full-file
goldens.

Answer: Use layered tests:

- Unit tests for typed domain objects, config defaults/migrations, project path
  resolution, marker detection, and SVG unit conversion.
- Renderer tests that assert generated SVG/SCAD contains expected module names,
  style attributes, generated-file headers, and high-level structure.
- Fixture integration tests using tiny SVG projects under `tests/fixtures/`,
  running `init`/`build` against a temp project root.
- Avoid full-file goldens at first except for tiny canonical snippets; prefer
  structural assertions to reduce test churn.
- Add a minimal watch-mode smoke test with a short timeout/temp file touch, but
  keep it reliable for CI.

