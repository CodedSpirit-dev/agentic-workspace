# Architecture decision output contract

Return a concise proposal with these sections:

1. **Scope and evidence** — software surface, relevant `REQ-*`/`SPC-*`, current
   repository observations, constraints, and unresolved facts.
2. **Candidate comparison** — one row per applicable method and decision
   boundary with 0–3 or `N/A` scores, evidence, conflicts, and migration cost.
   Do not hide rejected candidates or aggregate distinct software surfaces.
3. **Recommendation** — primary method per boundary, optional companions, and
   the exact repository, deployable, package, or module owned by each one.
4. **Rules** — allowed dependency direction, module or slice boundary, public
   API policy, shared-code threshold, and UI composition policy when relevant.
5. **Adoption** — incremental stages, preserved behavior, rollback or stop
   point, and who owns the migration in each affected repository or deployable.
6. **Proof and review** — lint/static checks, architecture tests, representative
   change exercise, risk signals, and dated reevaluation triggers.
7. **Traceability** — draft or accepted `DEC-*`, any `CONV-*`, `RSK-*`, and
   `VER-*`, each related to the requirements or specs that justify it.

A recommendation is incomplete if it names a method without dependency rules,
adoption cost, evidence, and conditions under which the choice should change.
