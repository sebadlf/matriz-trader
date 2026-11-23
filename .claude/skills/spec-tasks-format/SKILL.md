---
name: spec-tasks-format
description: Defines the exact line grammar Octo's orchestrator parses in tasks.md - the checkbox, the bare Tn id, the optional @agent-name, wave headings and how dependencies are declared. Apply this skill whenever writing, revising or ticking off task lines, and whenever appending a Critical Decision to a plan; a mis-formatted line is invisible to the runner.
---

# tasks.md format

Every line here is executed by the orchestrator, one run per task. A line it cannot
parse simply does not exist as far as Build is concerned.

## The task line

```
- [ ] T1: Add the format skill bodies - _outcome: four SKILL.md files seeded_
- [ ] T4 @frontend-implementer: Render the format-check strip above the gate bar
- [x] T2: Extract the default library into its own module
```

- A plain checkbox, `[ ]` open or `[x]` done.
- The **bare id** - `T1`, `T2`, ... - immediately after it. Never wrapped in emphasis:
  `- [ ] **T1**: ...` is not a task.
- Optionally `@agent-name` right after the id, and nowhere else - an `@name` later in
  the sentence is ignored.
- Then `:` and the description. End with `- _outcome: ..._` so the run knows what
  finishing looks like.

## Waves

```
## Wave 1
### Wave 2 (depends on T1)
```

Headings `##` to `####` are accepted, so a wave keeps working whether it came from the
plan (H3) or from the tasks template (H2). Everything in a wave runs **in parallel**,
so two tasks in the same wave must touch disjoint files. A wave starts only once every
task in every lower wave is done.

Dependencies come from three places: the wave itself, a parenthetical naming one task
(`(T3 depends on T1)`), or `depends on T1, T2` written inside the line.

## Sizing

One task is one verifiable change a single agent finishes in one run. If the outcome
needs the word "and", it is two tasks. Tasks that edit the same file belong in
different waves, or in one task.

## Ticking off, and recording deviations

Executing a task means editing `tasks.md` to flip its own `[ ]` to `[x]` - keep the
rest of the line byte-identical. If the work had to deviate from the plan, append to
`## Critical Decisions` at the end of `plan.md` (creating the heading if absent):

```
### Critical Decision - T3: Store the ledger per workspace
- **What**: keyed the version by workspace root, not globally.
- **Why**: a global key upgrades one workspace and silently skips the rest.
- **Affects**: the Affected files row for `electron/main.ts`.
```

Never rewrite the `## Tasks` section of the plan itself.
