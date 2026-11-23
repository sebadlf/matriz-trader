---
name: sdd-feature
description: Walk through requirements → plan → build for a new feature. Activate when the user wants to scope, plan, or break down a feature.
---

# SDD Feature Skill

When activated, drive a three-stage conversation. There are only **two gates**; the third stage is work, not a decision.

1. **Define** (`requirements.md`) — user stories and acceptance criteria in EARS notation. *Gate.*
2. **Plan** (`plan.md`) — approach with a mermaid diagram, affected files, the changes area by area with literal contracts, risks & rollback, verification, **and the dependency-ordered task waves**. *Gate.*
3. **Build** (`tasks.md`) — execute the waves, then ship.

There is no separate design document and no separate task-planning step: the plan carries both, and approving it derives `tasks.md` from its `## Tasks` section. Ask for confirmation before advancing a gate.

**Clarify before you plan.** If a decision would materially change the plan (library choice, data shape, migration strategy, a UX tradeoff), ask it *before* drafting: write 1–4 questions into the requirement document's `## Open Questions` and stop. Once those questions carry a **Resolved Decisions** entry — or the user says to proceed — draft the plan and never stop again: pick the reasonable default and record it in the plan.
