---
name: track-project
description: Track and report governed project execution across traditional phases, sprints, or flexible workstreams. Use for project status updates, standups, sprint or phase reviews, checkpoint closure, task and blocker triage, risk changes, plan drift, handoffs, and deciding whether a cycle or project is ready to close.
---

# Track a project

1. Read the project `index.md`, `status.md`, registry, current cycle, open
   tasks, risks, decisions, deliverables, and verifications.
2. Confirm that the current project owns the subject. Record related audits,
   inventories, historical analysis, new findings, decisions, deliverables,
   remediation, and acceptance evidence inside it rather than under `docs/` or
   a parallel plan.
3. Compare current evidence with the last status entry. Separate completed,
   in progress, blocked, changed, and unverified work.
4. Do not convert activity into progress unless a done condition or observable
   outcome changed.
5. Update status deterministically:

```bash
agentic-workspace/spec-kit/bin/project-kit status update <project> \
  --state <planned|active|blocked|at-risk|completed|archived> \
  --summary "<evidence-based summary>"
```

6. Update the active phase, sprint, or workstream with actual results,
   carryover, blockers, changed assumptions, and next verification.
7. Create a decision for material scope, mode, contract, or sequencing changes.
   Create or update risks instead of burying them in prose.
   Expand or clarify project scope when objective-required remediation is
   discovered; do not treat an initial task count as a permanent scope ceiling.
8. When `remediation-control` is enabled, maintain its finding, remediation,
   and verification IDs and the required `addresses`/`verifies` relations.
9. Close a cycle only when its exit criteria are evidenced. Move unfinished
   items explicitly; never rewrite the old cycle as if they completed.
10. Validate the registry and publish a concise status: outcome, evidence,
   blockers, decisions needed, next milestone, and confidence.
