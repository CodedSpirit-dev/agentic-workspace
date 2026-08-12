---
name: initiate-project
description: Create and bootstrap governed projects under agentic-workspace/projects in traditional, sprint, or flexible mode. Use when an initiative needs a durable objective, scope, requirements, cycles, tasks, decisions, risks, deliverables, evidence, multi-session tracking, or promotion from an ad-hoc task or plan.
---

# Initiate a project

1. Read `agentic-workspace/docs/project-management/index.md` and `modes.md`.
2. Confirm the objective, success criteria, scope, out-of-scope boundaries,
   owner, constraints, and known dependencies from real context. Mark missing
   facts `(TODO: confirm)`; do not invent them.
3. Select the least rigid honest mode:
   - `traditional` for ordered phase gates;
   - `sprint` for timeboxed backlog increments;
   - `flexible` for bounded workstreams or research checkpoints.
4. Select `minimal`, `standard`, or `complex`. Use `complex` only for multiple
   workstreams, agents, formal deliverables, or portable orders.
5. Run:

```bash
agentic-workspace/spec-kit/bin/project-kit init <name> \
  --mode <traditional|sprint|flexible> --profile <profile>
```

6. Fill the generated charter, requirements, plan, status, and first cycle.
   Create typed artifacts with the CLI; never allocate IDs or edit generated
   indexes manually.
7. Run `project-kit validate <project> --strict-index` and report unresolved
   intake questions separately from validation failures.

Promoting an existing task or plan must retain its original identifier and
source link in the project registry.
