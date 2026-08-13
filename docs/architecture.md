# Architecture

## Boundary

This repository is the product. Destination repositories are installations.
No installed procedure may require a source repository, a private path, an
environment file, or an organization-specific service.

```text
agentic-workspace repository
├── src/agentic_workspace/
│   ├── cli.py                   installer and update logic
│   └── payload/                 canonical installed content
└── tests/                       portability and migration contracts
             │
             └── install/update
                 ▼
destination repository
├── AGENTS.md / CLAUDE.md        thin entry points
├── agentic-workspace/           single source of truth
├── .agents/skills               Codex discovery adapters
├── .codex/agents + hooks.json   Codex adapters
├── .claude/skills + agents      Claude Code adapters
└── .hermes/skills + agents      Hermes adapters
```

## Ownership

- `src/agentic_workspace/payload/agentic-workspace/skills/` owns reusable workflows.
- `src/agentic_workspace/payload/agentic-workspace/agents/` owns bounded specialist prompts.
- `src/agentic_workspace/payload/agentic-workspace/spec-kit/` owns deterministic project state and
  validation.
- provider folders contain adapters only; they do not own policy.
- destination Git ignore rules may exclude regenerable provider adapters, but
  must not exclude canonical files under `agentic-workspace/skills/` or
  `agentic-workspace/agents/`; `agentic-workspace check` enforces this with
  `git check-ignore --no-index`.
- a destination project's `registry/project.json` owns IDs, states,
  relations, cycles, and status history.
- Markdown owns narrative, rationale, and evidence; generated indexes are
  views and must not be edited manually.

Stack- and domain-specific policy belongs to explicit extensions, not these
core ownership surfaces. The current limitations and proposed declarative
contract are documented in [`extensions.md`](extensions.md).

## Update contract

The installed `.managed-manifest.json` records hashes for product-managed
files. An update overwrites a file only when it is new, already equal to the
new payload, or still equal to the previously installed version. Local
modifications are preserved and reported. User-created projects and working
artifacts are never part of the managed payload.

`check` separately validates repository-owned projects with the installed
Project Kit, relative documentation links, and exact copies spanning canonical
documentation owners. These checks do not rewrite user content.

## Provider compatibility

Codex officially discovers repository skills under `.agents/skills`, custom
agents under `.codex/agents`, instructions from `AGENTS.md`, and lifecycle
hooks from `.codex/hooks.json`. The installer uses those surfaces and symlinks
skills because Codex follows symlinked skill folders. Claude Code and Hermes
receive adapters to the same canonical resources.
