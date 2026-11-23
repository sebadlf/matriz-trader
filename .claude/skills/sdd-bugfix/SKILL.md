---
name: sdd-bugfix
description: Reproduce → root cause → minimal fix workflow for bug specs. Activate when the user reports a bug or wants to scope a fix.
---

# SDD Bugfix Skill

Same three stages as a feature spec — `bugfix.md` → `plan.md` → `tasks.md` — with the analysis in place of requirements.

Capture three sections:

- **Current Behavior** — WHEN/THEN of the defect.
- **Expected Behavior** — WHEN/THEN/SHALL of the correct behavior.
- **Unchanged Behavior** — WHEN/THEN/SHALL CONTINUE TO statements that guard regressions.

Then plan: root cause, the minimal fix, and the waves that deliver it. Prefer the smallest possible change that satisfies the bugfix and preserves Unchanged Behavior, and make the regression guards explicit in **## Verification**.
