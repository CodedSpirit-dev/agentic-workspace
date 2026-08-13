# agentic-workspace

`agentic-workspace` is a standalone repository that installs the same project
operating system into any Git repository. It gives Codex, Claude Code, Hermes,
and humans one documentation index, one project registry, and one set of
versioned skills, agents, hooks, templates, and validation commands.

The source repositories used to design it are not runtime dependencies. The
installed workspace contains no Veza, MCP, ETL, Laravel, or POManager behavior
unless the destination repository documents and adds it explicitly.

## Install into a repository

After installing the Python package (POSIX example):

```bash
python3 -m pip install .
agentic-workspace install /path/to/repository
```

On Windows, use `py -3.11 -m pip install .`; the installed console commands
have the same names on every supported platform.

From a source checkout, the Python launcher works on Windows, Linux, and
macOS without installing the package:

```text
# Linux and macOS
python3 bin/agentic-workspace.py install /path/to/repository

# Windows
py -3.11 bin\agentic-workspace.py install C:\path\to\repository
```

The existing POSIX wrapper remains available on Linux and macOS:

```bash
./bin/agentic-workspace install /path/to/repository
```

Use `.` for the current repository. Re-running the same command performs an
idempotent update: unchanged managed files advance to the current version;
locally modified managed files and pre-existing adapters are preserved and
reported as conflicts.

The installer:

- creates `agentic-workspace/` with projects, docs, plans, tasks, tests,
  scripts, skills, agents, hooks, and the Spec Kit CLI;
- migrates existing `AGENTS.md` or `CLAUDE.md` content into preserved,
  indexed documentation;
- replaces root `AGENTS.md` with a short documentation pointer and makes
  `CLAUDE.md` point to it;
- exposes the canonical skills to Codex through `.agents/skills`, to Claude
  Code through `.claude/skills`, and to Hermes through `.hermes/skills`;
- renders project-specific Codex agents and exposes the same canonical agent
  prompts to Claude Code and Hermes;
- activates commit-policy hooks without replacing unrelated hook definitions.

Verify an installation with:

```bash
agentic-workspace check /path/to/repository
```

`check` also rejects ignored canonical skills or agents, broken relative
documentation links, exact cross-owner documentation copies, and invalid
projects discovered under `agentic-workspace/projects/`.

## Documentation ownership

Before creating a document, search for an existing project that owns the
subject. If none exists, use a bounded plan for coordinated work. Use
`agentic-workspace/docs/` only for durable repository knowledge that remains
valid after the work closes; do not mirror project status, findings, decisions,
inventories, or remediation there.

## Project modes

Each project under `agentic-workspace/projects/` selects one execution mode
while sharing the same traceability model:

| Mode | Work cadence | Mode-owned folder |
|---|---|---|
| `traditional` | Ordered phases and gates | `phases/` |
| `sprint` | Timeboxed backlog increments | `sprints/` |
| `flexible` | Independent workstreams and checkpoints | `workstreams/` |

All modes track requirements, tasks, decisions, risks, deliverables,
verifications, status history, and evidence in the project registry. They may
change cadence without discarding stable artifact IDs.

For a software project that needs an architecture decision, add the opt-in
`software-architecture` module and invoke `select-software-architecture`. It
compares FSD, Clean Architecture, Vertical Slice Architecture, Atomic Design,
and a simple package-by-layer baseline against the project's specs; it does not
impose one structure on every repository.

For an audit or improvement initiative that must prove every finding has a
disposition and acceptance evidence, add the opt-in `remediation-control`
module. Its active and completed states are validated against typed registry
relations instead of prose counts.

During implementation, invoke `develop-project` or the `project-developer`
agent. They locate the existing project owner before editing, keep newly
discovered objective-required work in that project, preserve architecture and
registry relationships, and require tests plus strict validation before status
transitions.

Create the first project after installation:

```bash
python3 agentic-workspace/spec-kit/bin/project-kit.py init my-project \
  --mode sprint --profile standard
```

If the Python package is installed, the shorter `project-kit` command invokes
the same bundled engine. The repository-local Python launcher is preferred in
automation because its engine and project templates advance together.

## Development

```bash
python3 -m pip install -e '.[test]'
python3 -m unittest discover -s tests -v
python3 -m unittest discover \
  -s src/agentic_workspace/payload/agentic-workspace/spec-kit/tests -v
```

See [`docs/architecture.md`](docs/architecture.md) for ownership boundaries
and [`docs/decisions/0001-portable-canonical-workspace.md`](docs/decisions/0001-portable-canonical-workspace.md)
for the initial architecture decision. Platform commands and distribution
expectations are in [`docs/platforms.md`](docs/platforms.md); the deliberately
unimplemented extension contract is in [`docs/extensions.md`](docs/extensions.md).
