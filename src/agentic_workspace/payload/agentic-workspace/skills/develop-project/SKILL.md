---
name: develop-project
description: Implement, debug, refactor, configure, migrate, or test code owned by a governed project while preserving its scope, artifact relationships, decisions, evidence, and status. Use when coding against project requirements, specs, tasks, findings, remediations, deliverables, or an active phase, sprint, or workstream; also use when implementation uncovers work omitted from the initial task list.
---

# Develop project work

1. Read `AGENTS.md`, `agentic-workspace/docs/documentation-routing.md`, and the
   smallest relevant repository documentation. Inspect Git status and preserve
   unrelated changes.
2. Search existing projects by subject, stable IDs, affected paths, and aliases,
   then search plans. Reuse the existing owner. Do not create a parallel plan,
   project, or `docs/` record for implementation already owned by a project.
3. Read the owning project's index, registry, status, current cycle, relevant
   requirements/specs, tasks, findings, decisions, risks, architecture
   assessment, and verification contract. Treat the project objective and
   accepted decisions as authoritative; an initial task count is not a scope
   ceiling.
4. Identify or create the typed `TSK-*` work item through Project Kit and relate
   it to the requirement, spec, finding, decision, or risk that justifies it.
   Record a new decision before materially changing scope, contract,
   architecture, migration behavior, or accepted sequencing.
5. Implement the smallest coherent change within the declared boundary. Follow
   enabled extension and architecture rules without silently imposing an
   optional method on projects that did not adopt it.
6. Run risk-proportionate tests and capture observable evidence. Do not equate
   activity, an exit code, a file's existence, or an HTTP response with
   behavioral acceptance.
7. Update task, deliverable, finding, risk, and verification states only when
   their evidence supports the transition. Keep inventories, analysis,
   remediation, decisions, deliverables, and acceptance evidence inside the
   owning project, never as parallel copies under `docs/`.
8. When `remediation-control` is enabled, relate each remediation to its listed
   finding with `addresses` and a listed verification to the remediation with
   `verifies`; do not declare the control complete until terminal states,
   verification methods, and evidence pass strict validation.
9. Regenerate indexes with Project Kit, run
   `project-kit validate <project> --strict-index`, then run
   `agentic-workspace check .`. Report outcome, changed artifacts, tests,
   evidence, unresolved risks, and the next governed step.

Never place secrets, `.env` values, generated graphs, credential-bearing output,
or unsupported progress claims in the project.
