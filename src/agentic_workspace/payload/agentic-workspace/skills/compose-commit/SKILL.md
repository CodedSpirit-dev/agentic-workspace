---
name: compose-commit
description: Draft a concise conventional commit message from the real staged diff without co-authorship or AI attribution. Use when asked to compose, review, amend, squash, or prepare a Git commit message; do not trigger merely because files changed when no commit work was requested.
---

# Compose a commit

1. Read `git status --short`, `git diff --cached`, and a small recent `git log`
   sample when scope conventions are unclear.
2. If staged changes touch agent instructions, documentation, projects, plans,
   skills, or agents, enforce `docs/documentation-routing.md`: check for an
   existing owner, parallel copies, broken links, ignored canonical sources,
   and invalid project registries. Run `agentic-workspace check .` when
   available. Report the blocker instead of composing a ready-to-use message
   when the ownership gate fails.
3. Describe the actual behavior or repository outcome, not diff mechanics.
4. Choose `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`,
   `perf`, or `style`. Reuse an established scope or omit it.
5. Write `type(scope): imperative subject`, preferably within 72 characters,
   without a trailing period. Add `!` only for a real breaking change.
6. Add a short body only when consequences or migration details are not clear
   from the subject.
7. Output only the message unless the user asks for explanation or a gate
   blocks commit readiness.

Never add `Co-Authored-By`, generated-by statements, model names, agent names,
or AI attribution. Never run commit, push, amend, reset, rebase, or squash
unless the user explicitly requests the operation.
