# Documentation routing and ownership

Choose one canonical owner before creating or moving a document.

## Precedence

1. Search `agentic-workspace/projects/` for an initiative that already owns the
   subject, system, decision, deliverable, audit, inventory, finding, or
   remediation. Store the work there and update its index and registry.
2. If no project owns it, search `agentic-workspace/plans/`. Reuse or create a
   bounded plan for coordinated work that does not yet need project governance.
3. Use `agentic-workspace/tasks/` for one small independent work item and
   promote it when coordination grows.
4. Use `agentic-workspace/docs/` only for durable repository architecture,
   commands, safety rules, conventions, or reference knowledge that remains
   valid after the related work closes.
5. Use `session-notes/` only for resumable context that has not become a
   durable decision or governed artifact.

Search by subject, stable IDs, affected paths, and aliases; a different title
does not establish different ownership. If two candidates appear to own the
same work, select one owner and record the consolidation or supersession.

## Gates

- Do not copy project status, task lists, scope, findings, inventories,
  decisions, deliverables, acceptance evidence, or remediation into `docs/`.
- Link to the canonical owner when durable documentation needs project context.
- An audit or newly discovered remediation belongs to the affected project;
  an initial list of tasks is not a ceiling on evidence needed to meet the
  project's objective.
- Preserve stable IDs and source links when promoting a task or plan.
- Before commit, check staged documentation for an existing owner, parallel
  copies, broken links, and ignored canonical skills or agents.

`agentic-workspace check` validates exact cross-owner copies and relative
links. Semantic overlap and ownership still require review by
`maintain-agent-docs` or `audit-project`.
