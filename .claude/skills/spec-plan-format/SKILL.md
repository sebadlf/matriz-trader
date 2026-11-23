---
name: spec-plan-format
description: Defines the exact markdown shape of plan.md - the objective line, mermaid Approach, Affected files table, area sections carrying literal contracts, Risks and rollback, Verification, the AC-n citations that drive traceability, and the ## Tasks waves that Build executes. Apply this skill whenever writing or revising a plan document; a plan whose ## Tasks section does not parse cannot be approved.
---

# plan.md format

Octo derives `tasks.md` from this file and traces every acceptance criterion through
it, so the structure is load-bearing. Produce exactly these sections, in this order.

## 1. Objective line

A single blockquote under the H1: `> One-line objective. Appetite: <S/M/L>. Risk: <low/medium/high>.`

## 2. `## Approach`

One ```mermaid flowchart, 3-7 nodes, **every label wrapped in quotes**
(`A["Reads spec"]`) - an unquoted label with punctuation fails to render. Then one
paragraph: the strategy chosen, and in one sentence each the alternatives rejected.

## 3. `## Affected files`

A table `| File | Change |`. Put real paths in backticks with a line number where you
have one - `` `src/lib/specTrace.ts:253` ``. A file reference is only picked up when it
is backticked *and* contains a `/` or a `:`; a bare `` `package.json` `` is not counted.

## 4. Area sections

One H2 per real boundary in *this* repo (`## Main process changes`,
`## Renderer changes`, ...) - not the placeholder names. Write the **literal contract**
each area commits to, as code, not prose: the exact type, signature, SQL or IPC shape.

## 5. `## Key implementation details`, `## Risks & rollback`, `## Verification`

Risks is a table `| Risk | Mitigation | How to revert |`. Verification maps every
acceptance criterion to how it is proven.

## 6. `## Tasks` - the section that gates approval

```
## Tasks

### Wave 1
- [ ] T1: <smallest verifiable change> - _outcome: ..._
- [ ] T2: <independent change, disjoint files> - _outcome: ..._

### Wave 2 (depends on T1)
- [ ] T3: <change> - _outcome: ..._
```

`## Tasks` is an **H2** and the waves under it are **H3**. The section ends at the next
H2, so `## Open Questions` and `## Critical Decisions` come after it. Approving the plan
copies this section verbatim into `tasks.md`; a `## Tasks` heading with prose and no
parsable task line is treated as absent and **blocks the gate**.

Task lines: a plain checkbox, the bare id, then a colon. Never wrap the id or the
checkbox in emphasis - `- [ ] **T1**: ...` does not parse. Name a specialist when the
task clearly belongs to one: `- [ ] T4 @frontend-implementer: ...`.

## 7. `## Open Questions`, then `## Critical Decisions`

Leave `## Critical Decisions` as an empty heading at the very end. Build appends to it
whenever a task deviates from this plan, which is what keeps the plan honest.

## Cite the criteria

Write `AC-n` into the rows, bullets and task lines that satisfy each one. Those
citations are what light up the Review view; without them it falls back to guessing by
vocabulary overlap, and guesses wrong.
