# Design

## Scope of work

Implement a safe, lightweight watch mode for the project workflow:

- `lettersign watch <name>` monitors the project input SVG and TOML config.
- Changes to watched inputs rebuild generated outputs:
  - `<name>.centerline.svg`,
  - `<name>_data.scad`,
  - projects-root `lettersign_common.scad`.
- User-owned files remain protected:
  - `<name>.scad` is created only if absent and never overwritten afterward,
  - `<name>.toml` is schema-managed by adding missing defaults without replacing
    existing values/comments.
- Watch mode should debounce changes and report build errors without exiting on
  transient save states.
- Add minimal timeout-bound tests for watch behavior and file safety.
- Update `README.md` for implemented watch behavior and generated/user-owned
  guarantees.

Out of scope:

- Manual post/centerline reconciliation.
- Watching generated SVG/SCAD output files.
- Multi-project watch orchestration.
- Destructive force modes.
- OpenSCAD rendering/mesh validation.

## File structure

```text
src/lettersign/
|-- cli.py        # watch command + --interval/--debounce/--once
|-- watcher.py    # polling watch loop, debounce, rebuild/error handling
|-- pipeline.py   # build function reused by watch
`-- errors.py     # user-facing Lettersign errors (missing SVG, validation, ...)

tests/
|-- test_watch.py # polling/watch + file-safety coverage
|-- test_cli.py   # includes watch CLI and option parsing
`-- test_pipeline.py # pipeline file safety guarantees

README.md         # watch usage and generated vs user-owned policy
```

## Conceptual architecture

```text
lettersign watch <name>
    |
    v
cli.cmd_watch(...)
    |
    |-- resolve project paths
    |-- ensure config exists / append missing defaults
    |-- require input SVG for initial build
    v
watcher.watch_project(...)
    |
    |-- initial build via existing pipeline
    |-- poll watched inputs: <name>.svg + <name>.toml
    |-- debounce changed mtimes
    |-- rebuild generated outputs only
    `-- on expected build errors: print concise stderr message and keep watching
```

The watch implementation should reuse the same build path as `lettersign build`
so file safety remains centralized:

- generated/overwritten: `<name>.centerline.svg`, `<name>_data.scad`,
  `projects/lettersign_common.scad`,
- user-owned/preserved: `<name>.scad`, existing TOML values/comments.

## Main components

### CLI

`watch` becomes a real command. It should accept:

- `--interval SECONDS`: polling interval, default small but not busy (for example
  `0.5`).
- `--debounce SECONDS`: delay after detecting a change before rebuilding, default
  around `0.2`.
- `--once`: perform the initial build and exit. This provides a CLI-level
  timeout-free smoke path for tests and scripts.

### Watch loop

`watcher.py` owns polling and debounce logic. Keep it small and deterministic:

- Watch only `paths.input_svg` and `paths.config_toml`.
- Snapshot file mtimes with `Path.stat().st_mtime_ns`; missing files should be
  represented explicitly.
- Always run an initial build before polling.
- After detecting a watched input change, wait for the debounce interval, then
  rebuild.
- Catch expected `LettersignError` failures from rebuilds, print a concise
  message to stderr, and continue watching.

Tests should avoid open-ended real-time loops where possible. Prefer:

- `--once` CLI smoke tests,
- small unit tests for mtime snapshot/change detection,
- a timeout-bound integration test that runs the watch loop for one detected
  change using tiny intervals.

### Documentation

README should describe:

- `uv run lettersign watch myletter`,
- optional `--interval`, `--debounce`, and `--once`,
- watched inputs (`<name>.svg`, `<name>.toml`),
- generated vs user-owned file behavior,
- errors during watch being reported while the loop keeps running.

# Phases

## Phase 1: Watch loop foundation and CLI options

[sub-agent: yes]

### Scope of phase

Implement the functional watch loop and CLI wiring.

In scope:

- Add `src/lettersign/watcher.py` with stdlib polling, debounce, initial build,
  expected-error reporting, and bounded/testable hooks.
- Update `src/lettersign/cli.py` so `lettersign watch <name>` is real and accepts
  `--interval`, `--debounce`, and `--once`.
- Reuse the existing `build_centerline_preview()` pipeline path so generated and
  user-owned file behavior remains centralized.
- Preserve existing `init`, `build`, top-level help, and legacy raw-SVG behavior.

Out of scope:

- Do not add watch dependencies.
- Do not watch generated outputs.
- Do not implement manual edit reconciliation or multi-project watch.
- Do not alter SCAD/SVG generation behavior except through the existing pipeline.

### Code Organization Reminders

- Prefer a granular file structure: `watcher.py` owns watch mechanics; `cli.py`
  only parses/dispatches.
- Place public dataclasses/functions first and helper functions at the bottom.
- Keep related functionality grouped together.
- Any temporary code should have a TODO comment so cleanup can find it later.

### Sub-agent Reminders

- Do not commit. The plan commits at the end as a single unit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- Do not disable, skip, or weaken existing tests to make the build pass.
- If something blocks completion, stop and report rather than improvising.
- Report back: what changed, what was validated, any deviations.

### Implementation Details

Read:

- `src/lettersign/cli.py`
- `src/lettersign/pipeline.py`
- `src/lettersign/errors.py`
- `docs/roadmaps/2026-04-28-lettersign-pipeline/m4-watch-file-safety/plan.md`

Create `src/lettersign/watcher.py` with public APIs similar to:

```python
@dataclass(frozen=True)
class WatchSettings:
    interval_seconds: float = 0.5
    debounce_seconds: float = 0.2
    once: bool = False

def watched_input_paths(paths: ProjectPaths) -> tuple[Path, Path]:
    return paths.input_svg, paths.config_toml

def snapshot_watched_inputs(paths: ProjectPaths) -> dict[Path, int | None]:
    ...

def watch_project(
    paths: ProjectPaths,
    *,
    settings: WatchSettings = WatchSettings(),
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    stop_after_rebuilds: int | None = None,
) -> None:
    ...
```

Implementation expectations:

- `watch_project()` should:
  - load/create config before every build so TOML defaults are refreshed and
    config edits are picked up,
  - require `paths.input_svg` before the initial build and raise
    `MissingInputSvgError` if it is absent,
  - run an initial build,
  - print a concise success line for initial and later builds,
  - return immediately if `settings.once` is true,
  - otherwise poll only `paths.input_svg` and `paths.config_toml`,
  - when snapshot changes, sleep for `debounce_seconds`, rebuild, then refresh
    the snapshot,
  - catch `LettersignError` during rebuilds after the initial build, print to
    stderr, and continue watching,
  - support `stop_after_rebuilds` for tests: count successful rebuild attempts
    including the initial build, and return once the count reaches that value.
- Keep sleep behavior injectable only if useful; avoid overengineering.
- Validate non-negative/non-zero intervals in CLI or `WatchSettings`. Prefer a
  simple `LettersignError` for invalid values.

Update `src/lettersign/cli.py`:

- Add parser options for `watch`:
  - `--interval` float default `0.5`,
  - `--debounce` float default `0.2`,
  - `--once` boolean flag.
- `cmd_watch()` should resolve the project and call `watch_project(...)`.
- Missing SVG should produce the same style of user-facing error as build.

### Validate

Run:

```bash
uv run pytest tests/test_cli.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

## Phase 2: Watch tests and file-safety coverage

[sub-agent: yes]

### Scope of phase

Add focused tests for watch behavior and file-safety guarantees.

In scope:

- Add `tests/test_watch.py` for watch internals and a timeout-bound smoke test.
- Extend `tests/test_cli.py` for `watch --once` and watch option parsing.
- Assert watch monitors only SVG/TOML and preserves user-owned wrapper SCAD.
- Assert expected build errors during watch are reported without exiting the loop.

Out of scope:

- Do not add new watch features.
- Do not use real long-running indefinite tests.
- Do not rely on external file-watch packages.
- Do not watch generated files.

### Code Organization Reminders

- Keep tests small, deterministic, and timeout-bound.
- Prefer unit tests for snapshot/change detection and one integration smoke test.
- Use temp directories; do not write into real `projects/` fixtures.
- Any temporary code should have a TODO comment so cleanup can find it later.

### Sub-agent Reminders

- Do not commit. The plan commits at the end as a single unit.
- Do not expand scope.
- Do not suppress warnings or weaken tests.
- Do not disable, skip, or weaken existing tests to make the build pass.
- If a test reveals an implementation mismatch, make the smallest scoped fix and
  report it.
- Report back: what changed, what was validated, any deviations.

### Implementation Details

Read:

- `src/lettersign/watcher.py`
- `src/lettersign/cli.py`
- `src/lettersign/pipeline.py`
- `tests/test_pipeline.py`
- `tests/test_cli.py`

Add `tests/test_watch.py` covering:

- `watched_input_paths()` returns exactly `(paths.input_svg, paths.config_toml)`.
- `snapshot_watched_inputs()` represents missing files as `None`.
- `watch_project(..., settings=WatchSettings(once=True))` performs one build and
  creates generated outputs.
- A custom wrapper created between builds is preserved by a later watch-triggered
  rebuild.
- A timeout-bound change test:
  - create a minimal project SVG/TOML,
  - start a thread that modifies the TOML or SVG after a short delay,
  - run `watch_project(..., interval_seconds=0.01, debounce_seconds=0.01,
    stop_after_rebuilds=2)`,
  - assert generated data changed or config-driven value updated.
- Error handling:
  - after initial successful build, briefly write invalid SVG or TOML,
  - trigger one watch rebuild,
  - assert a concise error appears on stderr and the loop can continue/return
    under a test stop condition.
  - If testing this precisely would be flaky, test the smaller error handling
    helper directly and keep one loop smoke test.

Extend `tests/test_cli.py`:

- `cli.main(["-p", tmp, "watch", "demo", "--once"])` creates the same generated
  outputs as build.
- Invalid `--interval 0` or negative debounce exits nonzero with a useful error
  if Phase 1 added validation.
- Existing `watch_is_stub` should be replaced/updated.

### Validate

Run:

```bash
uv run pytest tests/test_watch.py tests/test_cli.py -v
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

## Phase 3: README and cleanup validation

[sub-agent: supervised]

### Scope of phase

Update docs and perform final cleanup/validation for M4.

In scope:

- Update `README.md` with implemented watch behavior and file-safety policy.
- Move remaining planning notes to the bottom of this plan under `# Notes`.
- Add `# Decisions for future reference` to this plan.
- Remove temporary code, stale comments, and debug artifacts.
- Run full validation.

Out of scope:

- Do not add watch features.
- Do not implement manual reconciliation.
- Do not change public behavior beyond documentation or small cleanup fixes.

### Code Organization Reminders

- Keep docs accurate: distinguish implemented watch behavior from future
  reconciliation work.
- Keep `watcher.py` small and testable.
- Prefer user-facing wording around generated vs user-owned files.
- Leave no unexplained TODOs.

### Sub-agent Reminders

- Do not commit. The plan commits at the end as a single unit.
- Do not expand scope.
- Do not suppress warnings.
- Do not skip or weaken tests.
- Report files changed, validation commands/results, and deviations.

### Implementation Details

README should cover:

- `uv run lettersign watch myletter`.
- `--interval`, `--debounce`, and `--once`.
- Watch starts with an initial build.
- Watch monitors only `<name>.svg` and `<name>.toml`.
- Watch regenerates centerline SVG, data SCAD, and common SCAD helper.
- Watch preserves the user-owned wrapper SCAD and existing TOML values/comments.
- Expected errors are printed and watch continues.

Plan cleanup:

- Keep the `# Design` and `# Phases` sections.
- Move useful current-state/question notes under `# Notes` at the bottom.
- Add `# Decisions for future reference`:
  - record stdlib polling over a dependency,
  - record watching only SVG/TOML,
  - record `--once` as the CI/testable bounded mode.

Cleanup checklist:

- Search the diff for `TODO`, `pdb`, accidental debug prints, commented-out code,
  and non-ASCII punctuation.
- Confirm `projects/Y/Y.toml` remains untracked user data and is not part of the
  plan commit.
- Run full validation.

### Validate

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

# Decisions for future reference

- **Stdlib polling** - Watch uses repeated `mtime` checks and sleeps instead of a
  native file-notification dependency so CI stays simple and behavior stays easy
  to reason about.

- **Watched paths** - Poll only `<name>.svg` and `<name>.toml`; do not watch or
  depend on regenerated centerline SVG, data SCAD, wrapper SCAD, or the shared
  common helper changing on disk.

- **`--once` mode** - A single-invocation watch path performs the initial build
  and exits; tests and automation get a deterministic, timeout-free entry point.

# Notes

## Current implementation

- Watch lives in `src/lettersign/watcher.py`; `lettersign watch` is wired through
  `src/lettersign/cli.py` with `--interval`, `--debounce`, and `--once`.
- Watch calls the same `build_centerline_preview()` path as `build`, so wrapper
  creation/overwrite behavior and generated outputs stay identical.
- Timeout-bounded coverage lives in `tests/test_watch.py` alongside CLI coverage
  in `tests/test_cli.py`.
- Manual post/centerline reconciliation remains future roadmap work; watch does
  not ingest edited centerlines or marker overrides.

## Resolved planning questions

The confirmation questions from early M4 drafting are reflected in `# Decisions
for future reference` and the `# Design` / `# Phases` sections above.
