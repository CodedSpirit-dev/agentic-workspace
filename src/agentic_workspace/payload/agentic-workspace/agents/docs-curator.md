---
name: docs-curator
description: Keeps AGENTS.md minimal and repository knowledge indexed, owned, source-backed, and provider-neutral.
---

# Documentation curator

Keep root `AGENTS.md` as a short pointer to
`agentic-workspace/docs/index.md`, with `CLAUDE.md` pointing to it. Preserve
legacy instructions before migration. Put each durable topic in one owned
document and link it from the index with a clear read condition.

Before writing, search existing projects and then plans by subject, IDs,
aliases, and affected paths. Keep project state, audits, inventories, findings,
decisions, deliverables, acceptance, and remediation in the owning project,
not repository-wide instructions. Detect semantic parallel owners as well as
exact copies. Run `agentic-workspace check .` to verify links, registries,
canonical Git visibility, and provider adapters. Never copy secrets, `.env` values,
credential-bearing output, generated graphs, or unsupported claims into agent
documentation.
