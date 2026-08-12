from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PRODUCT = Path(__file__).resolve().parents[1]
GUARD = PRODUCT / "src/agentic_workspace/payload/agentic-workspace/hooks/providers/commit-message-guard.py"


class CommitGuardTests(unittest.TestCase):
    def run_guard(self, command: str):
        return subprocess.run(
            [str(GUARD)],
            input=json.dumps({"tool_input": {"command": command}}),
            text=True,
            capture_output=True,
        )

    def test_blocks_inline_coauthor(self):
        result = self.run_guard(
            "git commit -m 'docs: update' -m 'Co-Authored-By: Agent <a@example.com>'"
        )
        self.assertEqual(2, result.returncode)

    def test_allows_clean_commit(self):
        self.assertEqual(0, self.run_guard("git commit -m 'docs: update guide'").returncode)

    def test_ignores_non_commit_commands(self):
        self.assertEqual(0, self.run_guard("printf 'Co-Authored-By: example'").returncode)


if __name__ == "__main__":
    unittest.main()
