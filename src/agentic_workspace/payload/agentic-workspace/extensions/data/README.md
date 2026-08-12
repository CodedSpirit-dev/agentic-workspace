# Data extension

This extension contains optional conventions for data-oriented projects. None
of these conventions is a universal project gate.

Enable only the modules a project needs:

```bash
project-kit add-module agentic-workspace/projects/<project> column-dictionary
project-kit add-module agentic-workspace/projects/<project> metric-catalog
project-kit add-module agentic-workspace/projects/<project> migration-control
```

The same commands can be run without an installed Python package by replacing
`project-kit` with:

```text
# Linux and macOS
python3 agentic-workspace/spec-kit/bin/project-kit.py

# Windows
py -3.11 agentic-workspace\spec-kit\bin\project-kit.py
```

After opting in, apply the matching conditional checks in
`spec-kit/checklists/review-checklist.md`. SQL conventions remain guidance
until the repository explicitly adopts them.

- [`docs/sql-conventions.md`](docs/sql-conventions.md)
- [`docs/glossary.md`](docs/glossary.md)

The optional module declarations and templates currently live inside Spec Kit
for compatibility with its 2.1 engine. Their storage location does not make
them active in a project.
