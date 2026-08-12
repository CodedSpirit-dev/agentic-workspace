# Project model architecture

## Source of truth

```text
registry/project.json
├── identity, profile, mode, and project state
├── stable artifacts and explicit relations
├── phases, sprints, or workstreams
├── active cycles and status history
└── generated views: registry/index.md and status.md
```

Markdown artifacts own narrative and evidence. The registry owns identity,
state, path, and relationships.

## Modes

- `traditional`: ordered `phases/`; only one phase may be active.
- `sprint`: timeboxed `sprints/`; only one sprint may be active.
- `flexible`: independent `workstreams/`; multiple workstreams may be active.

Mode can change through a recorded decision without renumbering artifacts or
deleting old cycle history.

## Profiles

- `minimal`: core documents, tasks, decisions, and risks.
- `standard`: adds explorations, findings, specs, verifications, and
  deliverables.
- `complex`: adds analyses, project scripts, and portable agent orders.

Modules may be added later. Profiles share one model and are not incompatible
project types. `software-architecture` is an opt-in module for projects that
need a spec-driven architecture decision; no profile activates it implicitly.

## Artifact identity and relations

Stable IDs include `REQ-*`, `TSK-*`, `DEC-*`, `RSK-*`, `FND-*`, `SPC-*`,
`VER-*`, `DEL-*`, and `OUT-*`. Gaps are valid. Relations are explicit triples
such as `DEL-001 addresses REQ-002` and `VER-003 verifies DEL-001`.

Registry writes and order claims are atomic only inside one shared checkout.
Independent Git clones require external coordination and merge-conflict review.
