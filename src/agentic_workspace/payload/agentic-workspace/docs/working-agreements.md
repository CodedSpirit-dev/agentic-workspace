# Working agreements

## Before changing a repository

1. Read `AGENTS.md` and the relevant documentation index entries.
2. Inspect repository status and preserve unrelated local changes.
3. Identify affected consumers, tests, migrations, and documentation.
4. Record a project decision when a choice changes scope, contract, or future
   behavior.

## Evidence

- Do not fabricate commands, results, counts, dates, acceptance, or behavior.
- Mark unresolved claims as `(unverified)` or `(TODO: confirm)` and say what
  evidence would resolve them.
- Record commands and observable results for meaningful verification.
- Treat exit code zero as execution evidence, not automatically as behavioral
  acceptance.

## Safety

- Never store secrets or `.env` content in documentation, projects, orders,
  agent prompts, graphs, or logs.
- Resolve destructive targets before acting and document rollback when a
  change is hard to recover.
- Do not overwrite unrelated user changes or rewrite project history without
  explicit authorization.

## Scope and promotion

Use `tasks/` for bounded work, `plans/` for a short coordinated sequence, and
`projects/` when work gains multiple cycles, decisions, deliverables, agents,
dependencies, or durable evidence. Promotion preserves the original ID and
source context.
