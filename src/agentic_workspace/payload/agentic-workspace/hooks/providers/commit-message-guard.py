#!/usr/bin/env python3
"""Block provider shell calls that inline forbidden commit attribution."""

from __future__ import annotations

import json
import re
import sys


FORBIDDEN = re.compile(
    r"(?i)co-authored-by\s*:|generated\s+by\s+(?:claude|codex|chatgpt|gpt|ai)|"
    r"(?:claude|codex|chatgpt|openai|anthropic)\s+(?:agent|model)"
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    if "git commit" not in command:
        return 0
    if FORBIDDEN.search(command):
        print(
            "BLOCKED: commit messages may not contain Co-Authored-By or AI/agent attribution. "
            "Use the compose-commit skill.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
