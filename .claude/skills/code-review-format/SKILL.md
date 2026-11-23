---
name: code-review-format
description: Defines the exact findings block Octo parses out of a code review - one JSON array of findings with severity, file, line, title, detail and an optional suggestion. Apply this skill whenever reporting the result of a code review in Octo; findings written any other way are not shown.
---

# Code review format

Octo shows your review as a list of findings it can open, fix and post to a pull
request. It reads them from **one fenced `json` block** under a `## Findings` heading.
Prose outside that block is kept as the summary; anything inside it must parse.

## The shape

````
## Summary
Two or three sentences: what the change does and whether it is safe to merge.

## Findings
```json
[
  {
    "severity": "major",
    "file": "src/lib/tasks.ts",
    "line": 42,
    "title": "Wave heading regex drops H4 waves",
    "detail": "The pattern is anchored to ##/### so a #### wave is never parsed and its tasks never run.",
    "suggestion": "Use /^#{2,4}\s+Wave/ as the rest of the parser does."
  }
]
```
````

- `severity` is one of `blocker` (must not merge), `major` (a real bug or
  regression), `minor` (worth fixing, not dangerous) and `nit` (style or taste).
- `file` is the path **relative to the repository root**, exactly as the diff names it.
- `line` is a line number in the **new** version of the file and must fall inside a
  changed hunk - it is where the comment lands on a pull request. Omit it when the
  finding is about the file as a whole.
- `title` is one line; `detail` says what goes wrong and when; `suggestion` is the fix.
- No findings is a valid review: write `[]`.

## Judgement

Report what is wrong with the change, not a tour of it. Cite only code you read. A
finding without a concrete failure (`when X, Y happens`) is a `nit` at most. Do not
edit files - a review reports; fixing is a separate step the user chooses.
