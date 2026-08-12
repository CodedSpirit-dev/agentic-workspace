---
name: audit-project
description: Independently audit governed projects, registries, cycles, tasks, decisions, risks, deliverables, verifications, and closure gates. Use before a phase gate, sprint release, workstream closure, stakeholder handoff, production promotion, project completion, archive, or when documentation and implementation may have drifted.
---

# Audit a project

Remain read-only unless the user explicitly asks to repair findings.

1. Run `project-kit validate <project> --strict-index` and preserve its exact
   failures.
2. Trace every accepted deliverable to requirements and passed verifications.
   Trace every material scope or contract change to a decision.
3. Check the active phase, sprint, or workstream against its entry/exit
   criteria and actual evidence.
4. Check that status history matches observable repository state; flag stale,
   unsupported, or contradictory claims.
5. Review open tasks, blockers, risks, dependencies, unverified findings,
   secrets, generated outputs, and missing rollback or handoff detail.
6. Report findings by severity with artifact ID, path, evidence, impact, and
   required remediation. Avoid style-only findings.
7. Give one verdict: `PASS`, `PASS WITH CONDITIONS`, or `FAIL`. Do not mark a
   project or deliverable complete while a required gate lacks evidence.

If asked to repair, make each fix explicit, regenerate indexes through the CLI,
rerun validation, and preserve audit history.
