from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PRODUCT = Path(__file__).resolve().parents[1]
CLI = PRODUCT / "bin/agentic-workspace"
sys.path.insert(0, str(PRODUCT / "src"))

from agentic_workspace.cli import (  # noqa: E402
    Report,
    adapter_matches,
    digest_path,
    ensure_link,
    hook_is_runnable,
    provider_hook_command,
    save_manifest,
)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "destination"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", self.repo], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, ok=True):
        result = subprocess.run(
            [str(CLI), *map(str, args)], text=True, capture_output=True, cwd=PRODUCT
        )
        if ok and result.returncode:
            self.fail(
                f"command failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        if not ok and result.returncode == 0:
            self.fail(f"command unexpectedly passed: {args}")
        return result

    def test_clean_install_migrates_claude_and_wires_all_providers(self):
        legacy = "# Legacy instructions\n\nRun the real test suite.\n"
        (self.repo / "CLAUDE.md").write_text(legacy)
        self.run_cli("install", self.repo)

        agents = (self.repo / "AGENTS.md").read_text()
        self.assertIn("managed-by: agentic-workspace", agents)
        self.assertIn("agentic-workspace/docs/index.md", agents)
        self.assertIn("existing project first, then a bounded plan", agents)
        self.assertTrue(
            (self.repo / "agentic-workspace/docs/documentation-routing.md").is_file()
        )
        self.assertTrue((self.repo / "CLAUDE.md").is_symlink())
        self.assertEqual("AGENTS.md", os.readlink(self.repo / "CLAUDE.md"))
        self.assertEqual(
            legacy,
            (self.repo / "agentic-workspace/docs/imported/claude-original.md").read_text(),
        )
        self.assertIn(
            "claude-original.md",
            (self.repo / "agentic-workspace/docs/repository-guide.md").read_text(),
        )

        for skill_root in (".agents/skills", ".claude/skills", ".hermes/skills"):
            self.assertTrue((self.repo / skill_root / "track-project/SKILL.md").is_file())
            self.assertTrue((self.repo / skill_root / "develop-project/SKILL.md").is_file())
            self.assertTrue(
                (
                    self.repo
                    / skill_root
                    / "select-software-architecture/SKILL.md"
                ).is_file()
            )
        self.assertTrue((self.repo / ".codex/agents/project-steward.toml").is_file())
        self.assertTrue((self.repo / ".codex/agents/project-developer.toml").is_file())
        self.assertTrue((self.repo / ".codex/agents/software-architect.toml").is_file())
        self.assertTrue((self.repo / ".claude/agents/project-steward.md").is_symlink())
        self.assertTrue((self.repo / ".claude/agents/project-developer.md").is_symlink())
        self.assertTrue((self.repo / ".claude/agents/software-architect.md").is_symlink())
        self.assertTrue((self.repo / ".hermes/agents/project-steward.md").is_symlink())
        self.assertTrue((self.repo / ".hermes/agents/project-developer.md").is_symlink())
        self.assertTrue((self.repo / ".hermes/agents/software-architect.md").is_symlink())

        codex_hooks = json.loads((self.repo / ".codex/hooks.json").read_text())
        claude_settings = json.loads((self.repo / ".claude/settings.json").read_text())
        self.assertTrue(codex_hooks["hooks"]["PreToolUse"])
        self.assertTrue(claude_settings["hooks"]["PreToolUse"])
        hooks_path = subprocess.run(
            ["git", "-C", self.repo, "config", "--get", "core.hooksPath"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        self.assertEqual("agentic-workspace/hooks/git", hooks_path)
        self.run_cli("check", self.repo)

    def test_install_preserves_distinct_agents_and_claude_sources(self):
        agents = "# Codex rules\n\nRead architecture.\n"
        claude = "# Claude rules\n\nRun tests.\n"
        (self.repo / "AGENTS.md").write_text(agents)
        (self.repo / "CLAUDE.md").write_text(claude)
        self.run_cli("install", self.repo)
        self.assertEqual(
            agents,
            (self.repo / "agentic-workspace/docs/imported/agents-original.md").read_text(),
        )
        self.assertEqual(
            claude,
            (self.repo / "agentic-workspace/docs/imported/claude-original.md").read_text(),
        )

    def test_update_is_idempotent_and_preserves_local_work(self):
        self.run_cli("install", self.repo)
        project = self.repo / "agentic-workspace/projects/user-project/notes.md"
        project.parent.mkdir()
        project.write_text("user-owned\n")
        managed = self.repo / "agentic-workspace/docs/working-agreements.md"
        managed.write_text(managed.read_text() + "\nLocal extension.\n")

        result = self.run_cli("update", self.repo)
        self.assertIn("kept locally modified managed file", result.stderr)
        self.assertEqual("user-owned\n", project.read_text())
        self.assertIn("Local extension", managed.read_text())
        check = self.run_cli("check", self.repo, ok=False)
        self.assertIn("modified managed file", check.stdout)

    def test_update_preserves_locally_modified_agents_entry_point(self):
        self.run_cli("install", self.repo)
        agents = self.repo / "AGENTS.md"
        agents.write_text(agents.read_text() + "\nRepository-only safety rule.\n")

        result = self.run_cli("update", self.repo)

        self.assertIn("kept locally modified managed entry point: AGENTS.md", result.stderr)
        self.assertIn("Repository-only safety rule", agents.read_text())
        check = self.run_cli("check", self.repo, ok=False)
        self.assertIn("modified managed entry point: AGENTS.md", check.stdout)

    def test_rejects_symlinked_payload_root_that_escapes_target(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.repo / "agentic-workspace").symlink_to(outside, target_is_directory=True)

        result = self.run_cli("install", self.repo, ok=False)

        self.assertEqual(2, result.returncode)
        self.assertIn("path escapes target directory", result.stderr)
        self.assertEqual([], list(outside.iterdir()))

    def test_adapter_fallback_copies_files_and_directories(self):
        canonical = self.repo / "agentic-workspace/canonical"
        canonical.mkdir(parents=True)
        source_file = canonical / "agent.md"
        source_file.write_text("agent\n")
        source_dir = canonical / "skill"
        source_dir.mkdir()
        (source_dir / "SKILL.md").write_text("skill\n")
        report = Report(self.repo)

        with mock.patch.object(Path, "symlink_to", side_effect=OSError("unsupported")):
            ensure_link(
                self.repo / ".claude/agents/agent.md",
                "../../agentic-workspace/canonical/agent.md",
                report,
                source=source_file,
            )
            ensure_link(
                self.repo / ".claude/skills/skill",
                "../../agentic-workspace/canonical/skill",
                report,
                source=source_dir,
            )

        self.assertFalse((self.repo / ".claude/agents/agent.md").is_symlink())
        self.assertEqual("agent\n", (self.repo / ".claude/agents/agent.md").read_text())
        self.assertFalse((self.repo / ".claude/skills/skill").is_symlink())
        self.assertEqual("skill\n", (self.repo / ".claude/skills/skill/SKILL.md").read_text())

    def test_adapter_identity_does_not_depend_on_resolved_path_spelling(self):
        source = self.repo / "agentic-workspace/canonical.md"
        source.parent.mkdir()
        source.write_text("canonical\n")
        adapter = self.repo / ".claude/agents/canonical.md"
        adapter.parent.mkdir(parents=True)
        adapter.symlink_to("../../agentic-workspace/canonical.md")

        with mock.patch.object(
            Path,
            "resolve",
            side_effect=AssertionError("textual resolution must not be used"),
        ):
            self.assertTrue(adapter_matches(adapter, source))

    def test_manifest_paths_use_portable_separators(self):
        self.run_cli("install", self.repo)
        manifest = json.loads(
            (self.repo / "agentic-workspace/.managed-manifest.json").read_text()
        )
        for field in ("files", "links", "adapter_hashes", "generated_files"):
            self.assertTrue(manifest[field])
            self.assertTrue(all("\\" not in path for path in manifest[field]))

    def test_check_accepts_adapter_copy_and_rejects_missing_adapter(self):
        self.run_cli("install", self.repo)
        adapter = self.repo / ".agents/skills/track-project"
        source = self.repo / "agentic-workspace/skills/track-project"
        adapter.unlink()
        shutil.copytree(source, adapter)
        self.run_cli("check", self.repo)

        shutil.rmtree(adapter)
        result = self.run_cli("check", self.repo, ok=False)
        self.assertIn("disconnected managed adapter: .agents/skills/track-project", result.stdout)

    def test_check_rejects_ignored_canonical_skill_sources(self):
        self.run_cli("install", self.repo)
        (self.repo / ".gitignore").write_text("agentic-workspace/skills/\n")

        result = self.run_cli("check", self.repo, ok=False)

        self.assertIn("canonical source is ignored by Git", result.stdout)
        self.assertIn("agentic-workspace/skills/track-project/SKILL.md", result.stdout)

    def test_check_allows_ignored_regenerable_provider_adapters(self):
        self.run_cli("install", self.repo)
        (self.repo / ".gitignore").write_text(
            ".agents/\n.claude/\n.hermes/\n.codex/\n"
        )

        self.run_cli("check", self.repo)

    def test_check_strictly_validates_every_governed_project(self):
        self.run_cli("install", self.repo)
        launcher = self.repo / "agentic-workspace/spec-kit/bin/project-kit.py"
        subprocess.run(
            [
                sys.executable,
                str(launcher),
                "init",
                "broken-project",
                "--root",
                str(self.repo / "agentic-workspace/projects"),
                "--profile",
                "minimal",
            ],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=True,
        )
        self.run_cli("check", self.repo)
        (self.repo / "agentic-workspace/projects/broken-project/status.md").write_text(
            "stale\n"
        )

        result = self.run_cli("check", self.repo, ok=False)

        self.assertIn("project broken-project: status view is stale", result.stdout)

    def test_check_rejects_broken_links_and_exact_cross_owner_copies(self):
        self.run_cli("install", self.repo)
        plans = self.repo / "agentic-workspace/plans"
        plans.joinpath("broken.md").write_text("[missing](does-not-exist.md)\n")

        result = self.run_cli("check", self.repo, ok=False)
        self.assertIn("broken documentation link", result.stdout)

        plans.joinpath("broken.md").unlink()
        plans.joinpath("absolute.md").write_text("[private](C:\\private\\notes.md)\n")
        result = self.run_cli("check", self.repo, ok=False)
        self.assertIn("non-portable absolute documentation link", result.stdout)
        plans.joinpath("absolute.md").unlink()

        duplicate = "# Canonical state\n\nOne owner only.\n"
        self.repo.joinpath("agentic-workspace/docs/parallel.md").write_text(duplicate)
        project = self.repo / "agentic-workspace/projects/parallel"
        project.mkdir()
        project.joinpath("notes.md").write_text(duplicate)

        result = self.run_cli("check", self.repo, ok=False)
        self.assertIn("exact documentation copies cross canonical owners", result.stdout)
        self.assertIn("project parallel: missing registry/project.json", result.stdout)

    def test_unexpected_valid_hook_json_is_preserved_and_diagnosed(self):
        hook = self.repo / ".codex/hooks.json"
        hook.parent.mkdir()
        original = {"hooks": {"PreToolUse": {"legacy": True}}}
        hook.write_text(json.dumps(original))

        result = self.run_cli("install", self.repo)

        self.assertIn("unexpected PreToolUse value preserved", result.stderr)
        self.assertEqual(original, json.loads(hook.read_text()))
        check = self.run_cli("check", self.repo, ok=False)
        self.assertIn("commit policy hook is missing from .codex/hooks.json", check.stdout)

    def test_symlinked_hook_config_is_not_read_or_overwritten(self):
        outside = Path(self.temp.name) / "outside-hooks.json"
        outside.write_text('{"private": true}\n')
        codex = self.repo / ".codex"
        codex.mkdir()
        (codex / "hooks.json").symlink_to(outside)

        result = self.run_cli("install", self.repo)

        self.assertIn("symlinked hook configuration preserved", result.stderr)
        self.assertEqual('{"private": true}\n', outside.read_text())
        check = self.run_cli("check", self.repo, ok=False)
        self.assertIn("commit policy hook is missing from .codex/hooks.json", check.stdout)

    def test_invalid_manifest_structure_fails_closed(self):
        manifest = self.repo / "agentic-workspace/.managed-manifest.json"
        manifest.parent.mkdir()
        manifest.write_text(json.dumps({"files": ["not-a-map"]}))

        result = self.run_cli("check", self.repo, ok=False)

        self.assertEqual(2, result.returncode)
        self.assertIn("invalid managed manifest field files", result.stderr)

    def test_existing_hooks_path_requires_a_verifiable_chain(self):
        subprocess.run(
            ["git", "-C", self.repo, "config", "core.hooksPath", ".husky"],
            check=True,
        )
        result = self.run_cli("install", self.repo)
        self.assertIn("commit guard is disconnected", result.stderr)

        check = self.run_cli("check", self.repo, ok=False)
        self.assertIn("Git commit guard is disconnected", check.stdout)

        husky = self.repo / ".husky/commit-msg"
        husky.parent.mkdir()
        husky.write_text(
            "#!/bin/sh\nexec agentic-workspace/hooks/git/commit-msg \"$1\"\n"
        )
        husky.chmod(0o755)
        self.run_cli("check", self.repo)

    def test_dangling_manifest_symlink_cannot_escape_target(self):
        outside = Path(self.temp.name) / "outside-manifest.json"
        workspace = self.repo / "agentic-workspace"
        workspace.mkdir()
        (workspace / ".managed-manifest.json").symlink_to(outside)

        result = self.run_cli("install", self.repo, ok=False)

        self.assertEqual(2, result.returncode)
        self.assertIn("managed manifest must not be a symlink", result.stderr)
        self.assertFalse(outside.exists())

    def test_manifest_temporary_file_cannot_follow_predictable_symlink(self):
        workspace = self.repo / "agentic-workspace"
        workspace.mkdir()
        outside = Path(self.temp.name) / "outside-temporary.json"
        legacy_temporary = workspace / f"..managed-manifest.json.{os.getpid()}.tmp"
        legacy_temporary.symlink_to(outside)

        save_manifest(
            self.repo,
            {},
            {},
            {},
            {},
            {},
            Report(self.repo),
            git_hook_required=False,
        )

        self.assertFalse(outside.exists())
        self.assertTrue(legacy_temporary.is_symlink())
        self.assertTrue((workspace / ".managed-manifest.json").is_file())

    def test_preexisting_codex_agent_is_preserved_as_a_conflict(self):
        codex_agent = self.repo / ".codex/agents/project-steward.toml"
        codex_agent.parent.mkdir(parents=True)
        codex_agent.write_text('name = "repository_owned"\n')

        result = self.run_cli("install", self.repo)

        self.assertIn("generated adapter conflict preserved", result.stderr)
        self.assertEqual('name = "repository_owned"\n', codex_agent.read_text())
        check = self.run_cli("check", self.repo, ok=False)
        self.assertIn("missing or stale provider adapter", check.stdout)

    def test_nested_git_target_is_rejected_before_writes(self):
        nested = self.repo / "nested"
        nested.mkdir()

        result = self.run_cli("install", nested, ok=False)

        self.assertEqual(2, result.returncode)
        self.assertIn("target must be the Git worktree root", result.stderr)
        self.assertEqual([], list(nested.iterdir()))

    def test_non_executable_hook_with_canonical_substring_is_disconnected(self):
        self.run_cli("install", self.repo)
        subprocess.run(
            ["git", "-C", self.repo, "config", "core.hooksPath", ".husky"],
            check=True,
        )
        hook = self.repo / ".husky/commit-msg"
        hook.parent.mkdir()
        hook.write_text(
            "# This file mentions agentic-workspace/hooks/git/commit-msg but does not run it.\n"
        )
        hook.chmod(0o644)

        result = self.run_cli("check", self.repo, ok=False)

        self.assertIn("Git commit guard is disconnected", result.stdout)

    def test_hook_runnable_uses_platform_execution_semantics(self):
        hook = self.repo / "commit-msg"
        hook.write_text("#!/bin/sh\nexit 0\n")
        hook.chmod(0o644)

        self.assertFalse(hook_is_runnable(hook, "posix"))
        self.assertTrue(hook_is_runnable(hook, "nt"))

        hook.chmod(0o755)
        self.assertTrue(hook_is_runnable(hook, "posix"))

    def test_custom_hook_cannot_neutralize_guard_exit_status(self):
        self.run_cli("install", self.repo)
        subprocess.run(
            ["git", "-C", self.repo, "config", "core.hooksPath", ".husky"],
            check=True,
        )
        hook = self.repo / ".husky/commit-msg"
        hook.parent.mkdir()
        hook.write_text(
            "#!/bin/sh\n"
            "exec agentic-workspace/hooks/git/commit-msg \"$1\" || true\n"
        )
        hook.chmod(0o755)

        rejected = self.run_cli("check", self.repo, ok=False)
        self.assertIn("Git commit guard is disconnected", rejected.stdout)

        hook.write_text(
            "#!/bin/sh\nexec agentic-workspace/hooks/git/commit-msg \"$@\"\n"
        )
        self.run_cli("check", self.repo)
        subprocess.run(
            ["git", "-C", self.repo, "config", "user.email", "test@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", self.repo, "config", "user.name", "Test"], check=True
        )
        tracked = self.repo / "tracked.txt"
        tracked.write_text("content\n")
        subprocess.run(["git", "-C", self.repo, "add", "tracked.txt"], check=True)
        commit = subprocess.run(
            [
                "git",
                "-C",
                self.repo,
                "commit",
                "-m",
                "test: guarded commit",
                "-m",
                "Co-Authored-By: Agent <agent@example.com>",
            ],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(0, commit.returncode)
        self.assertIn("Co-Authored-By", commit.stderr)

    def test_provider_hook_requires_bash_matcher_and_command_type(self):
        hooks = self.repo / ".codex/hooks.json"
        hooks.parent.mkdir()
        hooks.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": "Read",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": provider_hook_command(),
                                    }
                                ],
                            }
                        ]
                    }
                }
            )
        )

        self.run_cli("install", self.repo)

        installed = json.loads(hooks.read_text())
        groups = installed["hooks"]["PreToolUse"]
        self.assertTrue(
            any(
                group.get("matcher") == "Bash"
                and any(
                    hook.get("type") == "command"
                    and hook.get("command") == provider_hook_command()
                    for hook in group.get("hooks", [])
                )
                for group in groups
            )
        )
        self.run_cli("check", self.repo)

    def test_provider_hook_uses_repository_local_platform_launcher(self):
        self.assertEqual(
            "./agentic-workspace/hooks/providers/commit-message-guard",
            provider_hook_command("posix"),
        )
        self.assertEqual(
            r"agentic-workspace\hooks\providers\commit-message-guard.cmd",
            provider_hook_command("nt"),
        )
        self.assertNotIn("python", provider_hook_command("posix").lower())

    @unittest.skipIf(os.name == "nt", "POSIX launcher selection test")
    def test_provider_launcher_falls_back_to_python_command(self):
        self.run_cli("install", self.repo)
        launcher = self.repo / "agentic-workspace/hooks/providers/commit-message-guard"
        fake_bin = Path(self.temp.name) / "fake-bin"
        fake_bin.mkdir()
        (fake_bin / "python").symlink_to(sys.executable)
        env = os.environ.copy()
        env["PATH"] = str(fake_bin)

        clean = subprocess.run(
            [str(launcher)],
            input=json.dumps({"tool_input": {"command": "git status"}}),
            text=True,
            capture_output=True,
            env=env,
        )
        self.assertEqual(0, clean.returncode, clean.stderr)

        blocked = subprocess.run(
            [str(launcher)],
            input=json.dumps(
                {
                    "tool_input": {
                        "command": "git commit -m 'x' -m 'Co-Authored-By: A <a@example.com>'"
                    }
                }
            ),
            text=True,
            capture_output=True,
            env=env,
        )
        self.assertEqual(2, blocked.returncode)
        self.assertIn("BLOCKED", blocked.stderr)

    def test_managed_fallback_copy_advances_with_canonical_source(self):
        source = self.repo / "agentic-workspace/canonical.md"
        source.parent.mkdir()
        source.write_text("version one\n")
        adapter = self.repo / ".codex/agents/canonical.md"
        report = Report(self.repo)
        with mock.patch.object(Path, "symlink_to", side_effect=OSError("unsupported")):
            ensure_link(
                adapter,
                "../../agentic-workspace/canonical.md",
                report,
                source=source,
            )
        previous_hash = digest_path(adapter)
        source.write_text("version two\n")

        with mock.patch.object(Path, "symlink_to", side_effect=OSError("unsupported")):
            ensure_link(
                adapter,
                "../../agentic-workspace/canonical.md",
                report,
                source=source,
                previous_hash=previous_hash,
            )

        self.assertEqual("version two\n", adapter.read_text())

    def test_preflight_prevents_partial_install_on_escaping_provider_directory(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.repo / ".codex").symlink_to(outside, target_is_directory=True)

        result = self.run_cli("install", self.repo, ok=False)

        self.assertEqual(2, result.returncode)
        self.assertIn("path escapes target directory", result.stderr)
        self.assertFalse((self.repo / "agentic-workspace").exists())
        self.assertFalse((self.repo / "AGENTS.md").exists())
        self.assertEqual([], list(outside.iterdir()))

    def test_dry_run_does_not_write(self):
        self.run_cli("install", self.repo, "--dry-run")
        self.assertFalse((self.repo / "agentic-workspace").exists())
        self.assertFalse((self.repo / "AGENTS.md").exists())

    def test_commit_hook_rejects_coauthor_trailer(self):
        self.run_cli("install", self.repo)
        message = self.repo / "message.txt"
        message.write_text("docs: add guide\n\nCo-Authored-By: Someone <x@example.com>\n")
        result = subprocess.run(
            [self.repo / "agentic-workspace/hooks/git/commit-msg", message],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Co-Authored-By", result.stderr)


if __name__ == "__main__":
    unittest.main()
