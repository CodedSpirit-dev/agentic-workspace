# Command reference

Run commands from a destination repository root. Examples use the installed
`project-kit` console command. Without the product package, replace
`project-kit` with the repository-local command for the host platform:

```text
# Linux and macOS
python3 agentic-workspace/spec-kit/bin/project-kit.py

# Windows
py -3.11 agentic-workspace\spec-kit\bin\project-kit.py
```

## Initialize and configure

```bash
project-kit init example --mode traditional --profile standard
project-kit init example --mode sprint --profile standard
project-kit init example --mode flexible --profile complex
project-kit init software-example --mode sprint --profile standard \
  --with software-architecture
project-kit add-module agentic-workspace/projects/example metric-catalog
project-kit add-module agentic-workspace/projects/example software-architecture
```

## Cycles and project status

```bash
project-kit cycle list agentic-workspace/projects/example
project-kit cycle start agentic-workspace/projects/example SPR-001
project-kit cycle close agentic-workspace/projects/example SPR-001 \
  --evidence VER-002 --evidence evidence/review.md
project-kit cycle create agentic-workspace/projects/example --title "Next increment"
project-kit status update agentic-workspace/projects/example \
  --state active --summary "SPR-002 started after review."
project-kit status show agentic-workspace/projects/example
```

## Artifacts and relations

```bash
project-kit create <project> requirement --title "Observable outcome"
project-kit create <project> task --title "Implement bounded change"
project-kit decision create <project> --title "Select approach" --status accepted
project-kit create <project> risk --title "Dependency may slip"
project-kit create <project> deliverable --title "Release package"
project-kit create <project> verification --title "Acceptance check" --status passed \
  --method "pytest tests/acceptance" --evidence evidence/acceptance.txt
project-kit relate <project> DEL-001 addresses REQ-001
project-kit relate <project> VER-001 verifies DEL-001
project-kit artifact set-status <project> DEL-001 accepted
```

## Validation and migration

```bash
project-kit validate <project> --strict-index
project-kit index <project>
project-kit audit <project>
project-kit audit <project> --write-report
project-kit migrate <legacy-project> --dry-run
project-kit migrate <legacy-project> --apply
```

## Agent orders

```bash
project-kit order create <project> --domain repo --title "Execute bounded change" \
  --scope "Declared files" --out-of-scope "Unrelated systems"
project-kit order ready <project> REPO-0001
project-kit order claim <project> REPO-0001 --agent worker-1
project-kit order start <project> REPO-0001
project-kit order record-result <project> REPO-0001 --result result.json
project-kit order verify <project> REPO-0001 --verification VER-001
project-kit order close <project> REPO-0001
```

`--evidence` accepts an exact registered artifact ID or a path to a file inside
the project. Free-form claims and paths that escape the project are rejected.
A `passed` verification requires both a method and resolvable evidence. Use
`artifact set-status ... passed --method ... --evidence ...` when evidence is
added after the verification artifact was created.

`validate`, including `--strict-index`, and `audit` are read-only. Stale
generated views are reported with a suggestion to run `index`; they are never
silently repaired. `audit --write-report` is the explicit opt-in that writes
`registry/audit-report.md`.

`order claim --recover-expired` recovers only an expired lease. It never
overrides a live claim. A recorded result must satisfy
`schemas/order-result.schema.json` before it can change order state.
