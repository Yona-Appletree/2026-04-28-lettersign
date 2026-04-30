# lettersign Pipeline Roadmap - Decisions

#### Project-based workflow

- **Decision:** Operate on `projects/<name>/` with `<name>.svg`, `<name>.toml`,
  generated `<name>.centerline.svg`, generated `<name>_data.scad`, and
  user-owned `<name>.scad`.
- **Why:** The real workflow is editing a sign project over time, not invoking a
  one-off SVG conversion script.
- **Rejected alternatives:** Raw SVG path CLI only (does not model config or
  generated/user-owned files); global config (does not fit per-sign dimensions).

#### Command-first CLI

- **Decision:** Use `lettersign init <name>`, `lettersign build <name>`, and
  `lettersign watch <name>`.
- **Why:** Explicit commands are easy to script and leave room for smart project
  defaults without hiding destructive behavior.
- **Rejected alternatives:** Single overloaded command (ambiguous as behavior
  grows); only file-path commands (not project-oriented).
- **Revisit when:** The CLI is stable enough to add `lettersign <name>` as a
  convenience alias for `build`.

#### TOML config ownership

- **Decision:** Use `tomlkit` to preserve user config comments/formatting while
  adding missing schema defaults.
- **Why:** Python's stdlib `tomllib` cannot write TOML or preserve comments, but
  the project config should remain user-owned and readable.
- **Rejected alternatives:** `tomllib` only (read-only); overwrite whole TOML
  files (destroys user edits/comments).

#### Millimeter geometry units

- **Decision:** Normalize internal/output geometry to millimeters. Use SVG
  metadata scale when available; otherwise assume `1 SVG unit = 1 mm`.
- **Why:** Config values and OpenSCAD dimensions are naturally millimeter-based,
  and SVG metadata is not always available.
- **Rejected alternatives:** Keep raw SVG units throughout (makes SCAD/config
  confusing); require explicit scale in every config (too much ceremony).
- **Revisit when:** Real project SVGs show inconsistent metadata that needs a
  more explicit scale override UX.

#### Generated versus user-owned files

- **Decision:** Overwrite generated centerline SVG and `<name>_data.scad`; create
  `<name>.scad` only if absent; update `<name>.toml` only by adding missing
  schema defaults.
- **Why:** The pipeline needs repeatable outputs without destroying the user's
  customization layer.
- **Rejected alternatives:** Never overwrite any outputs (stale generated data);
  overwrite wrappers/config wholesale (unsafe for user edits).

#### SCAD data/wrapper split

- **Decision:** Put generated modules in `<name>_data.scad`, shared helpers in a
  common SCAD file, and user customization in `<name>.scad`.
- **Why:** This matches the desired workflow: generated geometry can refresh
  freely while the user can customize the top-level model.
- **Rejected alternatives:** One monolithic generated SCAD file (hard to
  customize safely); no shared helper file (duplicates post/common modules).

#### Deferred manual edit reconciliation

- **Decision:** Defer manual centerline/post reconciliation from v0, but design
  generated outputs so it can be added later.
- **Why:** The likely UX needs careful thought: users may move/delete/create
  posts or trim centerline segments, and regenerated candidates may need a
  color-based accept/reject flow.
- **Rejected alternatives:** Implement reconciliation immediately (too much
  uncertainty); ignore manual edits permanently (does not match the workflow).
- **Revisit when:** Users start editing generated centerline/post SVGs by hand.

#### Structural tests over broad goldens

- **Decision:** Prefer unit tests and structural renderer assertions over
  full-file golden tests for most SVG/SCAD output.
- **Why:** Generated formatting will evolve, and tests should catch behavior
  regressions without creating constant churn.
- **Rejected alternatives:** Full-file goldens everywhere (brittle); only
  end-to-end tests (poor diagnostics).

