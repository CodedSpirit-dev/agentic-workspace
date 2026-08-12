# New Project Checklist

Run this after scaffolding a project with `project-kit init`. Verify every
applicable item; do not mark the project ready while a required item remains
unchecked.

- [ ] Project folder name is kebab-case and describes the domain, not the date
      (e.g. `returns-cost-analysis`, not `2026-07-investigation`).
- [ ] `registry/project.json` exists and declares schema version, profile,
      enabled modules, counters, artifacts, and relations.
- [ ] Every file required by the selected profile and enabled modules exists.
      Legacy projects without a registry may still use the historical ten-file
      checklist during migration.
- [ ] `index.md` is the canonical entry point. Any additional overview file
      links to it and does not define conflicting status or policy.
- [ ] `index.md` links to every other file — none is orphaned.
- [ ] `requirements.md` has the stakeholder ask as an exact quote, a business
      objective, success criteria, and explicit out-of-scope — none left
      blank (unknowns are marked `(TODO: confirm)`, never empty).
- [ ] `index.md`'s Status block is present in the exact grep-able format and
      set to the correct starting value (usually `exploration`).
- [ ] No empty subfolders exist (`sql/`, `deliverables/`, etc. are created
      only when their first file lands).
- [ ] No working artifact (`.sql`, script, spreadsheet, supplementary
      analysis) sits loose at the project root — anything beyond the
      canonical file set lives in a purpose-named subfolder.
- [ ] Filenames are kebab-case unless an enabled extension documents a
      required ecosystem convention.
- [ ] Every unknown at creation time is marked `(TODO: confirm)`, not left
      blank.
- [ ] `project-kit validate <project> --strict-index` returns `PASS`.
