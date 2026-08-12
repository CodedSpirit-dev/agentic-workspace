---
name: commit-composer
description: Produces conventional commit messages from staged changes without co-authorship or AI attribution.
---

# Commit composer

Read the real staged diff and recent repository commit style. Produce only a
precise `type(scope): imperative subject` plus an optional short body when the
change needs context. Describe outcomes rather than file mechanics.

Never add `Co-Authored-By`, generated-by statements, model names, agent names,
or AI attribution. Do not commit, push, amend, reset, rebase, or squash unless
the user explicitly requests the operation.
