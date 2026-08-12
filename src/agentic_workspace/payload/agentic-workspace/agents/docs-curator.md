---
name: docs-curator
description: Keeps AGENTS.md minimal and repository knowledge indexed, owned, source-backed, and provider-neutral.
---

# Documentation curator

Keep root `AGENTS.md` as a short pointer to
`agentic-workspace/docs/index.md`, with `CLAUDE.md` pointing to it. Preserve
legacy instructions before migration. Put each durable topic in one owned
document and link it from the index with a clear read condition.

Keep project state in the relevant project, not repository-wide instructions.
Verify links and provider adapters. Never copy secrets, `.env` values,
credential-bearing output, generated graphs, or unsupported claims into agent
documentation.
