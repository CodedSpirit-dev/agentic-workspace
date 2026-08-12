---
name: select-software-architecture
description: Evaluate software project specifications and propose a traceable architecture method or bounded hybrid. Use when starting a software project, defining or revisiting architecture, choosing between Feature-Sliced Design, Clean Architecture, Vertical Slice Architecture, Atomic Design, or package-by-layer organization, or when growth and coupling make the current structure questionable.
---

# Select Software Architecture

Select an architecture from project evidence, not fashion or framework habit.
The result is a proposal until an authorized owner accepts its decision record.

## Workflow

1. Confirm that the scope is a software application, service, or library. For a
   governed project, read `charter.md`, `requirements.md`, relevant `SPC-*`,
   constraints, risks, current architecture, team capabilities, and expected
   change patterns. Mark missing facts `(TODO: confirm)`.
2. Read
   `agentic-workspace/extensions/software/docs/architecture-methods.md`,
   `selection-guide.md`, and `references/decision-output.md`. Do not treat
   Atomic Design as a complete application architecture, package-by-layer as a
   formal standard, or FSD as identical to backend Vertical Slice Architecture.
3. If the owner adopts a durable assessment and the governed project does not
   list `software-architecture`, enable it explicitly. Without authorization to
   change project state, report the command but do not run it:

```bash
agentic-workspace/spec-kit/bin/project-kit add-module <project> software-architecture
```

4. Separate observed facts, assumptions, and unanswered questions. Identify
   the software surface, business volatility, domain complexity, dependency
   volatility, delivery boundaries, UI reuse needs, team experience, current
   coupling, and migration budget.
5. Score every applicable candidate for one declared decision boundary with the
   same criteria. Mark non-applicable criteria `N/A`; do not treat them as zero
   or total scores across frontend, backend, libraries, or design systems.
   Exclude a candidate only with spec or repository evidence. A hybrid is valid
   only when each method owns a different boundary, such as FSD for frontend
   module placement and Atomic Design inside UI segments. A multi-surface
   product may have one primary method per separately owned boundary.
6. Complete `software-architecture.md` with a primary recommendation, bounded
   companions, alternatives rejected, dependency rules, enforcement checks,
   migration stages, costs, risks, owners, and reevaluation triggers. Define a
   shared-code extraction trigger from observed change patterns; leave it
   `(TODO: confirm)` rather than inventing a numeric threshold. Do not
   reorganize production code as part of this selection workflow.
7. For a governed project, create a draft `DEC-*` and relate it to the source
   `REQ-*` or `SPC-*` with `DEC-* derived_from REQ-*|SPC-*`. Record enforceable
   rules as `CONV-*`, uncertainty as `RSK-*`, and observable architecture checks
   as `VER-*`. List those IDs in the assessment frontmatter and use
   `project-kit relate`; never hand-edit generated indexes. Change
   `assessment_status` to `proposed` only when its source and decision links
   validate, and to `accepted` only with owner authorization, active conventions,
   and a verification plan.
8. Run `project-kit validate <project> --strict-index`. Report the proposal,
   evidence, unresolved questions, artifact IDs, and exact trigger for the next
   review.

## Guardrails

- Prefer the smallest architecture that protects the change axes present in
  the specs. Complexity without a forcing constraint is a cost, not rigor.
- Distinguish logical dependency rules from folder names. Clean Architecture
  requires inward source dependencies; it does not mandate one universal tree.
- Preserve a working incumbent architecture unless measured pain or upcoming
  requirements justify migration.
- Define automated checks where tooling permits, but do not claim a boundary is
  enforced when it is only documented.
- Keep framework, language, and vendor recommendations outside the decision
  unless project constraints make them relevant.
