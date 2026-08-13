# Review Checklist

The operational rubric behind `audit.md` entries and the `project-auditor`
agent. Walk every applicable section; report in the
PASS/FAIL/WARNINGS/Verdict format below. One line per item — no filler.

## PASS conditions

- `registry/project.json` validates against the v2 model; every registered
  artifact exists, every relation resolves, and IDs/aliases are unique.
- Generated indexes match the structured registry.
- If agent orders are enabled, every `context.json` has a matching generated
  `order.md`; closed orders have `result.json`, verification, an execution
  log, and a consistent completion marker.

- Every requirement in `requirements.md` traces to a plan phase, a finding or
  decision, and (if shipped) a deliverable-manifest row.
- Every `decision-log.md` entry is numbered sequentially, dated, and has
  Context/Decision/Alternatives Considered/Rationale.
- Every open question anywhere in the project is either struck through with
  `**Answered:**` + an evidence link, or still open and marked `(TODO:
  confirm)` — none silently missing.
- Every unsourced claim carries `(unverified)` or `(TODO: confirm)`.
- `index.md`'s Status line matches the project's actual state.
- No working artifact sits loose at the project root; everything lives in a
  purpose-named subfolder, and `index.md` reflects the real layout.

## Conditional module checks

Apply these only when the corresponding optional module is listed in
`registry/project.json`:

- `column-dictionary`: the Markdown and YAML views agree on names, aliases,
  types, and meanings.
- `metric-catalog`: every formula deviation has a reason and approver.
- `migration-control`: every row has a current status, owner, and date.
- `software-architecture`: the assessment cites project requirements or specs,
  compares applicable methods with one rubric, assigns distinct boundaries to
  any hybrid, and its frontmatter status agrees with the registered `DEC-*`,
  enforceable conventions, risks, verifications, and relations required by that
  state.
- `remediation-control`: every listed finding is reached from a typed
  remediation through `addresses`, every remediation has a listed verification,
  and a completed control uses terminal dispositions plus passed verification
  method and evidence.
- Any installed extension: every release or audit gate declared by that
  extension has evidence. An extension must not silently add universal rules.

## FAIL conditions

- A file required by the selected profile/module is missing.
- A registry ID is duplicated, a relation is broken, a state is invalid, or
  a registered artifact file is missing.
- An order contains a likely secret, has a conflicting claim, or closes
  without required result/verification evidence.
- A deliverable exists with no requirement it satisfies (orphan deliverable).
- An irreversible operation is proposed without declared authorization,
  blast radius, verification, and a recovery path.
- A decision-log entry has been edited to reverse its own conclusion instead
  of superseded by a new entry.
- Project-owned status, audits, inventories, findings, decisions, deliverables,
  remediation, or acceptance evidence have a parallel owner under `docs/` or
  another plan.

## WARNINGS

- An open question has been unresolved for an unusually long time relative to
  the project's pace.
- An enabled module records a material deviation without a matching decision.
- `index.md`'s "Last updated" date is far behind the most recent finding.
- A working-artifact subfolder mixes more than one phase/decision (e.g. a
  superseded fix beside live artifacts) without a semantic subdivision, or a
  past reorganization left dangling references to pre-move paths.

## Output format

```
## Documentation Review: <project_name>

### PASS
### FAIL
### WARNINGS
### Verdict: PASS | NEEDS FIXES
```
