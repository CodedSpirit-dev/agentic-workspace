---
name: track-project
description: Track and report governed project execution across traditional phases, sprints, or flexible workstreams. Use for project status updates, standups, sprint or phase reviews, checkpoint closure, task and blocker triage, risk changes, plan drift, handoffs, and deciding whether a cycle or project is ready to close.
---

# Track a project

1. Read the project `index.md`, `status.md`, registry, current cycle, open
   tasks, risks, decisions, deliverables, and verifications.
2. Compare current evidence with the last status entry. Separate completed,
   in progress, blocked, changed, and unverified work.
3. Do not convert activity into progress unless a done condition or observable
   outcome changed.
4. Update status deterministically:

```bash
agentic-workspace/spec-kit/bin/project-kit status update <project> \
  --state <planned|active|blocked|at-risk|completed|archived> \
  --summary "<evidence-based summary>"
```

5. Update the active phase, sprint, or workstream with actual results,
   carryover, blockers, changed assumptions, and next verification.
6. Create a decision for material scope, mode, contract, or sequencing changes.
   Create or update risks instead of burying them in prose.
7. Close a cycle only when its exit criteria are evidenced. Move unfinished
   items explicitly; never rewrite the old cycle as if they completed.
8. Validate the registry and publish a concise status: outcome, evidence,
   blockers, decisions needed, next milestone, and confidence.
