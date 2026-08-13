# Provider adapters

The canonical resources live under `agentic-workspace/`. Provider folders are
discovery and configuration adapters only.

| Consumer | Instructions | Skills | Agents | Hooks |
|---|---|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills` | `.codex/agents/*.toml` | `.codex/hooks.json` |
| Claude Code | `CLAUDE.md -> AGENTS.md` | `.claude/skills` | `.claude/agents` | `.claude/settings.json` |
| Hermes | `AGENTS.md` | `.hermes/skills` | `.hermes/agents` | canonical scripts as supported |

Do not edit symlinked copies. Edit the canonical skill or agent and run the
installer's update command to refresh rendered provider files.

Canonical `agentic-workspace/skills/**` and `agentic-workspace/agents/**` files
must remain visible to Git so the procedures persist across clones. Provider
adapter folders may be ignored when they are regenerated locally. Run
`agentic-workspace check .` after changing ignore rules; its failure names the
canonical path and matching rule. Use `git check-ignore --no-index -v <path>`
to inspect precedence before adding the narrowest necessary negation to the
repository's `.gitignore`.

Provider hook configuration invokes a managed repository-local launcher, not
a hard-coded `python` or `python3` command. The POSIX and Windows launchers
select an available Python 3 runtime and propagate the policy guard's exit code
without masking a rejected commit.
