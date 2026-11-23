---
name: spec-bugfix-format
description: Defines the exact markdown shape of bugfix.md - Reproduction, Current Behavior, Expected Behavior, Unchanged Behavior regression guards and Environment, with EARS-numbered AC-n criteria. Octo parses this shape literally, so apply this skill whenever writing or revising a bug analysis document, even for a one-line change.
---

# bugfix.md format

A bug spec is parsed by the same machinery as a feature spec, so the same literal rules
apply - with one inversion that matters more than any other.

## Sections

Use these H2 headings, spelled exactly, in this order:

`## Reproduction` - `## Current Behavior (defect)` - `## Expected Behavior` -
`## Unchanged Behavior (regression guards)` - `## Environment` - `## Open Questions`

There are **no user stories** in a bug spec; criteria are grouped by the section they
came from instead.

## The inversion: Current Behavior must not say SHALL

`SHALL` is what marks a line as an acceptance criterion. The defect is not something
the system is supposed to do, so describing it with `SHALL` would file the bug itself
as a requirement. Write it as plain WHEN/THEN:

```
- WHEN the workspace path contains a space THEN the CLI subprocess exits with code 127.
```

## Expected and Unchanged

Both carry numbered `AC-n` criteria containing `SHALL`. Unchanged Behavior uses the
`SHALL CONTINUE TO` form - these are the regression guards, and `## Verification` in
the plan has to prove each one still holds.

```
- AC-1: WHEN the workspace path contains a space THEN the system SHALL launch the CLI successfully.
- AC-2: WHEN the workspace path contains no space THEN the system SHALL CONTINUE TO launch the CLI successfully.
```

## The rest

`## Reproduction` is a numbered list, one action per step, ending with what you
actually observe. `## Environment` records the versions, OS and configuration that
made the bug appear - a bug that only reproduces under one of them is a different bug.

Only unindented list items are parsed, and criteria under `## Open Questions` or
`## Resolved Decisions` are ignored by design.

Prefer the smallest change that satisfies Expected Behavior without disturbing
Unchanged Behavior. A bug spec that grows a feature is scope creep, and the audit
flags it.
