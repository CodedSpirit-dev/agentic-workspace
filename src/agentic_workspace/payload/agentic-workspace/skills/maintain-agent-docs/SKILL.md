---
name: maintain-agent-docs
description: Migrate, organize, index, and audit repository instructions shared by Codex, Claude Code, Hermes, and humans. Use when converting CLAUDE.md to AGENTS.md, reducing oversized root instructions, adding repository architecture or commands, fixing stale documentation indexes, or deciding where durable agent knowledge belongs.
---

# Maintain agent documentation

1. Read `agentic-workspace/docs/documentation-routing.md`. Search existing
   projects by subject, stable ID, affected path, and alias, then search plans.
   Reuse the existing owner before creating or moving any document.
2. Treat root `AGENTS.md` as a short entry point. It should direct agents to
   `agentic-workspace/docs/index.md`, not duplicate architecture or procedures.
3. Keep `CLAUDE.md` as a relative symlink to `AGENTS.md` when supported.
4. Before replacing existing instructions, preserve exact source content under
   `agentic-workspace/docs/imported/` and link it from `repository-guide.md`.
5. Move only durable repository architecture, setup, commands, safety
   constraints, and conventions into one owned document. Keep project status,
   audits, inventories, findings, decisions, deliverables, acceptance, and
   remediation in their existing project; do not mirror them under `docs/`.
6. Add each durable document to `docs/index.md` with one line explaining when
   to read it. Avoid duplicate owners and self-referential index chains.
7. Keep claims source-backed and technical identifiers exact. Mark unresolved
   material explicitly.
8. Run `agentic-workspace check .` after changes. Resolve broken links, exact
   cross-owner copies, invalid projects, and ignored canonical skill or agent
   sources before declaring the documentation ready.

Do not copy secrets, `.env` values, machine-local credentials, generated
graphs, or large terminal output into documentation.
