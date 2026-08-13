# Project artifacts

| Artifact | Purpose | Closure evidence |
|---|---|---|
| Requirement | Defines a needed outcome or constraint | Accepted or explicitly superseded |
| Task | Bounded work with an owner and done condition | Observable result or linked output |
| Decision | Preserves context, alternatives, and consequence | Accepted rationale and affected links |
| Risk | Tracks probability, impact, mitigation, and owner | Mitigated, accepted, or closed rationale |
| Deliverable | Names a formal output and its consumer | Acceptance criteria plus verification |
| Verification | Tests a claim or deliverable | Reproducible method and result |
| Finding | Records a source-backed observation | Evidence reference and resolved, rejected, superseded, or archived disposition |
| Output | Captures generated working material | Reproduction command or source |

The registry owns identity, state, path, and relations. Markdown owns narrative
and evidence. A deliverable cannot be accepted without a requirement relation
and a passed verification.

When `remediation-control` is active, findings, remediation artifacts, and
acceptance verifications must also appear in its frontmatter and satisfy its
directed `addresses` and `verifies` graph.
