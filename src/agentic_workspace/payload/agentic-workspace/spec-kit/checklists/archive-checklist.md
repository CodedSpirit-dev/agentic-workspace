# Archive Checklist

Run when a project's subject is abandoned, superseded, or deleted (see
`docs/lifecycle.md` state 8).

- [ ] The reason for archiving is documented in `index.md` (or `findings.md`
      if the reason itself is a finding worth dating).
- [ ] If anything was deleted, the affected artifact IDs, blast radius, and
      tested recovery or restore procedure are recorded.
- [ ] Every open question still unresolved is explicitly marked deferred —
      not silently dropped. State who, if anyone, owns picking it back up.
- [ ] `index.md`'s Status flips to `archived` (or `deleted`, if the subject
      itself no longer exists anywhere).
- [ ] All cross-links from other projects into this one still resolve, or are
      updated to point at the archive location.
- [ ] The project history stays in its governed project folder. If repository
      policy requires a physical move, leave a resolvable `index.md` pointer
      at the original path and update the registry evidence.
- [ ] Registered artifacts and orders use terminal `archived`, `cancelled`,
      `superseded`, or `closed` states as appropriate; history is preserved.
- [ ] Any enabled `remediation-control` records an honest terminal disposition
      for every governed finding; archiving the project does not silently erase
      an unresolved finding.
