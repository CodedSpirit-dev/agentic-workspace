# Software architecture extension

This optional extension helps agents select and govern an architecture for a
software project from its specifications. Installation does not activate it and
it adds no universal folder rule.

Enable its project assessment explicitly:

```bash
project-kit add-module agentic-workspace/projects/<project> software-architecture
```

Then invoke `select-software-architecture` or the `software-architect` agent.
The assessment is stored in the project as `software-architecture.md`; the
actual choice belongs in a traceable `DEC-*` with any enforceable `CONV-*`,
risks, and verifications.

Read:

- [`docs/architecture-methods.md`](docs/architecture-methods.md) for method
  scope, rules, strengths, costs, and combinations;
- [`docs/selection-guide.md`](docs/selection-guide.md) for the evidence-based
  selection and verification procedure.
