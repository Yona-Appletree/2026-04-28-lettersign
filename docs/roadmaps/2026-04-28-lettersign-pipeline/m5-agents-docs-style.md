# Milestone 5: AGENTS.md, docs, and style guidance

## Goal

Capture the project's coding and workflow preferences so future agents keep the
code typed, organized, readable, and aligned with the intended user workflow.

## Suggested plan location

`docs/roadmaps/2026-04-28-lettersign-pipeline/m5-agents-docs-style/`

No plan file required.

## Scope

### In scope

- Add `AGENTS.md` with guidance for:
  - typed Python,
  - small single-purpose files,
  - domain objects and high-level concepts first,
  - utilities after domain concepts,
  - clean error checking,
  - tests for new behavior,
  - generated/user-owned file boundaries.
- Update `README.md` to describe the project-based workflow:
  - `lettersign init <name>`,
  - `lettersign build <name>`,
  - `lettersign watch <name>`,
  - generated centerline SVG and SCAD outputs.
- Document the initial config properties and defaults.
- Document the generated file policy.

### Out of scope

- Code refactors not needed for documentation accuracy.
- Detailed CAD design documentation for posts/channels beyond current behavior.

## Key decisions

- `AGENTS.md` is project guidance, not implementation planning.
- Documentation should describe the stable workflow and call out known deferred
  manual-edit reconciliation work.

## Deliverables

- `AGENTS.md`.
- README updates.
- Any small docs updates needed to keep the CLI/config workflow discoverable.

## Dependencies

- Should happen before Milestones 1-4 so future implementation work inherits the
  desired code style and generated/user-owned file guidance.
- README should distinguish current behavior from planned roadmap behavior until
  the project CLI and SCAD pipeline are implemented.

## Execution strategy

**Option A - Direct execution (no plan file).**

Justification: Direct: small documentation-only milestone with clear outputs and
no open design questions.

**Suggested chat opener:**

> I can implement this milestone without planning. Here is a summary
> of decisions/questions: <bulleted list>. If you agree, I will
> implement now using a Composer 2 sub-agent. If you want to discuss
> any of these, let me know now.

