---
name: maintain-agent-docs
description: Migrate, organize, index, and audit repository instructions shared by Codex, Claude Code, Hermes, and humans. Use when converting CLAUDE.md to AGENTS.md, reducing oversized root instructions, adding repository architecture or commands, fixing stale documentation indexes, or deciding where durable agent knowledge belongs.
---

# Maintain agent documentation

1. Treat root `AGENTS.md` as a short entry point. It should direct agents to
   `agentic-workspace/docs/index.md`, not duplicate architecture or procedures.
2. Keep `CLAUDE.md` as a relative symlink to `AGENTS.md` when supported.
3. Before replacing existing instructions, preserve exact source content under
   `agentic-workspace/docs/imported/` and link it from `repository-guide.md`.
4. Move durable repository architecture, setup, commands, safety constraints,
   and conventions into one owned document. Keep work-specific state in its
   project, plan, task, or session note.
5. Add each durable document to `docs/index.md` with one line explaining when
   to read it. Avoid duplicate owners and self-referential index chains.
6. Keep claims source-backed and technical identifiers exact. Mark unresolved
   material explicitly.
7. After changes, verify all relative links, instruction entry points, skill
   adapters, and provider agent adapters.

Do not copy secrets, `.env` values, machine-local credentials, generated
graphs, or large terminal output into documentation.
