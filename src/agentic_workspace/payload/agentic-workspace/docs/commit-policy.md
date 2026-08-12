# Commit policy

Compose messages from the actual staged diff. Use:

```text
type(scope): imperative subject

- optional high-level consequence
```

Allowed types are `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`,
`chore`, `perf`, and `style`. Omit scope when the change is genuinely
cross-cutting.

`Co-Authored-By` trailers are forbidden, regardless of whether they name a
human, model, agent, or tool. Do not add generated-by statements or AI/model
attribution. The configured Git identity is the sole author.

Never commit, push, reset, rebase, or amend unless the user explicitly asks
for that operation.
