# Agentic workspace

This directory is the repository-local source of truth for agent procedures
and project execution. Start with [`docs/index.md`](docs/index.md).

## Stable surfaces

- `projects/`: governed projects in traditional, sprint, or flexible mode.
- `plans/`: short-lived repository-wide plans not yet promoted to a project.
- `tasks/`: small bounded work items; promote them when coordination grows.
- `session-notes/`: resumable context that is not yet a durable decision.
- `tests/`: workspace-policy and procedure tests.
- `scripts/`: repository-local automation supporting procedures.
- `archive/`: closed auxiliary artifacts; governed projects keep their own
  durable history in place.
- `skills/`, `agents/`, `hooks/`: canonical multi-provider workflows.
- `spec-kit/`: deterministic project registry, templates, and validators.
- `extensions/`: optional stack- and domain-specific procedures; installation
  alone does not activate their rules.

Do not place secrets, `.env` content, access tokens, private dumps, or
credential-bearing command output anywhere under this directory.
