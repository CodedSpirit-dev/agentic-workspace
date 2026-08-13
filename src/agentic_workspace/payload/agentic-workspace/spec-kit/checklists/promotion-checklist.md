# Promotion Checklist

Run before a project instance graduates from exploration/analysis into a
standing production artifact (see `docs/lifecycle.md` state 8).

- [ ] The `project-auditor` agent (or a manual walk of `review-checklist.md`)
      returns **PASS** on the project's current state.
- [ ] `project-kit validate <project> --strict-index` returns **PASS**.
- [ ] Every mutative agent order required for promotion is `closed`, has a
      structured result, and cites verification evidence.
- [ ] `deliverable-manifest.md` is complete — every shipped output has a row,
      each citing the requirement(s) it satisfies.
- [ ] Stakeholder sign-off is recorded in `deliverable-manifest.md`.
- [ ] If the optional `migration-control` module is enabled, its final status
      is recorded for every governed object; no required row remains pending.
- [ ] If `remediation-control` is enabled, its status is `completed` and all
      listed findings, remediations, and verifications pass strict validation.
- [ ] `plan.md`'s Promotion section is filled: target path, objects
      created/modified, irreversible-operation flags, and a link to the
      passing audit entry.
- [ ] `index.md`'s Status flips to `promoted to production` (or your repo's
      equivalent label).
- [ ] Every enabled extension-specific release gate also passes. Record the
      command, tool version, result, and evidence reference rather than naming
      a reviewer that may not exist in another repository.
- [ ] The project folder is **left in place** — it is the decision-log anchor
      for whatever it became, not a scratch file to delete.
- [ ] If the promoted artifact has a doc-comment or README of its own, it
      cross-links back to this project folder.
