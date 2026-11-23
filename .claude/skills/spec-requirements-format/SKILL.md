---
name: spec-requirements-format
description: Defines the exact markdown shape of requirements.md - the H2 sections, US-n user stories, numbered EARS AC-n criteria and their (US-n) back-references. Octo parses this shape literally, so apply this skill whenever writing or revising a feature requirements document, even when the user only asks to add or reword a single criterion.
---

# requirements.md format

Octo *parses* this document rather than reading it. Every rule below exists because a
parser depends on it; break one and the Review view, the traceability graph or the
phase gate silently stops working.

## Sections

Use these H2 headings, spelled exactly, in this order:

`## Introduction` - `## User Stories` - `## Acceptance Criteria (EARS notation)` -
`## Out of Scope` - `## Non-Functional Requirements` - `## Open Questions`

Only `##` opens a section. A `###` heading stays *inside* the section above it.

## User stories

One per top-level list item:

```
- US-1: As a <role>, I want <capability>, so that <outcome>.
```

The `As a ... I want ... so that ...` wording is matched literally - reword it and the
story stops being a story. Number them `US-1`, `US-2`, ...

## Acceptance criteria

One per top-level list item: numbered `AC-1`, `AC-2`, ..., containing the word `SHALL`,
and ending with the story it answers in parentheses.

```
- AC-1: WHEN the user submits an empty form THEN the system SHALL keep the draft and show one error per invalid field. (US-1)
- AC-2: WHILE a run is streaming THE system SHALL disable the Approve button. (US-2)
```

Four EARS forms are recognised; anything else is flagged as *not EARS*:

| Form | Shape |
|---|---|
| Event | `WHEN <trigger> THEN the system SHALL <response>` |
| State | `WHILE <state> THE system SHALL <continuous behavior>` |
| Unwanted | `IF <precondition> THEN the system SHALL <response>` |
| Optional | `WHERE <feature is present> the system SHALL <response>` |

Every story needs at least one criterion, and every criterion needs a story - the
Review view lists both kinds of orphan.

## Two things that silently break parsing

- **Indented bullets are invisible.** Only unindented list items are read, so a
  criterion nested under its story is not a criterion at all.
- **`SHALL` inside `## Open Questions` or `## Resolved Decisions` is ignored** by
  design. Never write a criterion there.

## Untestable wording

A criterion has to be checkable by someone who did not write it. These words are
flagged: *user-friendly, easy to use, intuitive, seamless, responsive, snappy, fast,
quickly, performant, efficient, robust, reliable, appropriate, reasonable, as needed,
if necessary, properly, nicely, modern, clean, simple, several, various, etc.*

Replace the judgement with something observable - not "responds quickly" but "responds
within 200 ms"; not "handles several items" but "handles at least 50 items".
