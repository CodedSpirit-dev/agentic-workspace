# Project management standard

Every governed initiative lives at `agentic-workspace/projects/<name>/` and
chooses one delivery mode. The mode controls cadence, not traceability.

## Shared project contract

Every mode has:

- an objective, scope, success criteria, constraints, owner, and status;
- stable IDs for requirements, tasks, decisions, risks, deliverables,
  verifications, findings, and outputs;
- explicit relations between work and its evidence;
- a status history and an audit gate before closure;
- a place for scripts and generated outputs without treating output as proof.

See [`modes.md`](modes.md) for mode selection and [`artifacts.md`](artifacts.md)
for artifact ownership.

Audits, inventories, historical analyses, findings, remediation, and acceptance
evidence remain inside the project that owns their subject. When an initiative
requires complete finding disposition, enable the opt-in
`remediation-control` module; it validates `FND-*` →
`TSK-*`/`DEC-*`/`RSK-*` → `VER-*` traceability through registry relations.

Use `initiate-project` to create or promote an owner, `develop-project` while
implementing its governed work, `track-project` for evidence-based status, and
`audit-project` for an independent gate. These skills share the same routing
and registry contract instead of creating provider-specific project records.

## Commands

```bash
agentic-workspace/spec-kit/bin/project-kit init <name> --mode traditional
agentic-workspace/spec-kit/bin/project-kit init <name> --mode sprint
agentic-workspace/spec-kit/bin/project-kit init <name> --mode flexible

agentic-workspace/spec-kit/bin/project-kit cycle create \
  agentic-workspace/projects/<name> --title "Cycle objective"
agentic-workspace/spec-kit/bin/project-kit status update \
  agentic-workspace/projects/<name> --state active --summary "Observed status"
agentic-workspace/spec-kit/bin/project-kit validate \
  agentic-workspace/projects/<name> --strict-index
```
