---
name: record-decision
description: Record, supersede, and trace durable project decisions. Use when choosing architecture, scope, delivery mode, naming, data contracts, priorities, risk acceptance, implementation approach, migration behavior, or any alternative that future agents must understand instead of rediscovering.
---

# Record a decision

1. Identify the concrete choice and the work it affects. Do not record a
   preference as accepted until the authorized decision exists.
2. Gather the forcing context, alternatives actually considered, evidence,
   decision owner, date, consequences, and reversal conditions.
3. Create the ID through the CLI:

```bash
agentic-workspace/spec-kit/bin/project-kit decision create <project> \
  --title "<decision>" --status <draft|accepted>
```

4. Fill the generated document. Link affected requirements, risks, tasks,
   deliverables, and verifications with `project-kit relate`.
5. When the choice changes, create a new decision and use `decision supersede`;
   never rewrite accepted history.
6. Validate the project and state whether the decision is draft, accepted, or
   still awaiting authorization.

Never include credentials, private tokens, or unsupported retrospective
rationale.
