---
name: manage-deliverable
description: Register, trace, verify, accept, hand off, supersede, or archive formal project deliverables. Use for releases, reports, migrations, documentation packages, datasets, designs, runbooks, deployed features, or any output that must satisfy requirements and retain acceptance evidence.
---

# Manage a deliverable

1. Distinguish a working output from a deliverable. Generated files belong in
   `output/`; a formal consumer-facing result requires a `DEL-*` artifact.
2. Create the deliverable with `project-kit create <project> deliverable
   --title "<title>"` and state its consumer, format, location, owner,
   acceptance criteria, reproducibility, and rollback or supersession path.
3. Link it to at least one requirement with `addresses` or `implements` and to
   its source artifacts with `derived_from` or `produces`.
4. Create an independent `VER-*` artifact, execute the stated verification,
   record actual evidence, and relate it with `verifies`.
5. Mark the deliverable `verified` or `accepted` only after the corresponding
   evidence exists. A file's existence, HTTP 200, or exit code zero alone is
   not acceptance.
6. Add the handoff location and remaining limitations to the manifest. Keep
   prior versions linked when superseded.
7. Run strict validation before reporting readiness.
