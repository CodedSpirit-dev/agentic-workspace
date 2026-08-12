# Project Spec Kit

The Project Spec Kit is the deterministic project engine inside
`agentic-workspace`. It creates traditional, sprint, or flexible projects
over one registry model with stable IDs, explicit relations, cycles, status
history, validation, and portable agent orders.

```bash
python3 agentic-workspace/spec-kit/bin/project-kit.py init example \
  --mode sprint --profile standard
python3 agentic-workspace/spec-kit/bin/project-kit.py validate \
  agentic-workspace/projects/example --strict-index
```

These examples use the POSIX `python3` name. On Windows, use `py -3.11` and
Windows path separators. The extensionless Bash wrapper is retained for POSIX
shells, and an installed product package exposes the cross-platform
`project-kit` console command.

The CLI owns identity, state, indexes, and lifecycle transitions. Markdown
owns objectives, rationale, plans, and evidence. Never edit generated
`registry/index.md` or `status.md` manually.

Read [`docs/architecture.md`](docs/architecture.md),
[`docs/lifecycle.md`](docs/lifecycle.md), and
[`docs/command-reference.md`](docs/command-reference.md).
