# Glossary

**`(unverified)`** — a claim in a document that has not yet been checked
against a real source. Marked inline, next to the claim itself, not in a
separate caveats section. Removed only when replaced by evidence — never
just deleted once someone "is pretty sure."

**`(TODO: confirm)`** — a known gap: a fact that is expected to be
verifiable, but hasn't been checked yet. Distinct from `(unverified)` in that
it usually names what specifically needs confirming (a query to run, a
person to ask).

**Decision log** — the append-only, numbered record of choices made during a
project (`decision-log.md`, entries `D-001, D-002, ...`). Each entry is
permanent; a later change of mind is a new entry that references the one it
supersedes, never an edit to the original. See Principle P-5 in
[`constitution.md`](../constitution.md).

**Traceability chain** — the line connecting a stakeholder requirement to
the plan phase that addresses it, to the finding or decision that resolved
it, to the deliverable that shipped it. `audit.md` and the `project-auditor`
agent exist primarily to check that this chain has no broken links.

**Promotion** — a project instance graduating from exploration or analysis
into a maintained deliverable. The project's documentation folder is left in
place afterward as the historical record and decision-log anchor.

**Archive** — a project instance whose subject was abandoned, superseded, or
deleted. Distinct from promotion in that nothing new was produced; the
documentation records why the project ended and, if applicable, exactly how
to restore whatever was removed.

**Canonical entry point** — the one file, used identically across every
project instance, that a reader opens first (`index.md` in the default
profile).

**Extension** — an optional, versioned package of stack- or domain-specific
procedures. Installing or enabling an extension may add documented checks;
its conventions never become universal core rules implicitly.

**Audit vs. review** — an *audit* is the periodic, dated, recorded check
(an entry in `audit.md`) that a project still satisfies its own constitution
and traceability requirements. A *review* is the act of performing that
check, typically by walking `checklists/review-checklist.md` or invoking the
`project-auditor` agent. Every review that completes should produce an
audit entry; not every audit entry requires the full agent (a light
self-check may suffice between gate audits).
