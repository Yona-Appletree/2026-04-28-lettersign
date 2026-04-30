### What was built

- OpenSCAD generation on `lettersign build <name>`: normalized centerline SVG plus **`projects/<name>/<name>_data.scad`** (always overwritten), **`projects/lettersign_common.scad`** at the projects root (synced from the package on each build), and **`projects/<name>/<name>.scad`** (created only when missing, never overwritten afterward).
- Per source path (`path1`, `path2`, etc.): **`pathN_outline()`**, **`pathN_channel()`**, **`pathN_posts()`**, **`pathN_3d()`**; channel geometry is the **global** centerline buffered with round caps/joins (`led_channel_width`, `line_resolution`), **clipped** to that path's outline; posts use marker radius (**5 mm**) and **`post_height`**.
- Assembler module **`{sanitized_project_name}_3d()`** in the data file invokes every **`pathN_3d()`**; default wrapper **`use`**s **`{name}_data.scad`** and calls that assembler.
- Structural tests across **`render_scad`**, **`scad_geometry`**, packaged common SCAD assets, pipeline, CLI, and project paths (no broad full-file SCAD goldens).
- **`README.md`** documents generated vs user-owned files and SCAD behavior for M3.

### Decisions for future reference

#### Shared helper location

The common SCAD helper lives **once** at **`projects/lettersign_common.scad`** (projects root). Each **`{name}_data.scad`** uses **`use <../lettersign_common.scad>`**. The canonical source is **`src/lettersign/scad/lettersign_common.scad`** in the Python package and is copied to the projects tree on build (not duplicated per project folder).

#### Wrapper ownership

**`<name>.scad`** is **user-owned** after creation: the tool creates it only if absent and must **never** overwrite it on later builds. **`<name>_data.scad`** and **`lettersign_common.scad`** are regenerated every build.

#### Per-path channel from a global centerline (M3)

Per-path **`pathN_channel()`** polygons come from clipping the **global** buffered centerline to each normalized source-path outline, not separate per-path centerline solves (see M3 Q1).

#### Packaging

Bundled **`*.scad`** ship as setuptools **package data** (`lettersign.scad` / **`scad_assets`**) so `build` writes a consistent **`lettersign_common.scad`** beside project directories.
