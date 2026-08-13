from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import venv
import zipfile


PRODUCT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.dist_a = cls.root / "dist-a"
        cls.dist_b = cls.root / "dist-b"
        cls._build(cls.dist_a)
        cls._build(cls.dist_b)
        cls.wheel = next(cls.dist_a.glob("*.whl"))
        cls.sdist = next(cls.dist_a.glob("*.tar.gz"))

        cls.venv_root = cls.root / "venv"
        venv.EnvBuilder(with_pip=False).create(cls.venv_root)
        scripts = cls.venv_root / ("Scripts" if os.name == "nt" else "bin")
        cls.python = scripts / ("python.exe" if os.name == "nt" else "python")
        cls.agentic_workspace = scripts / (
            "agentic-workspace.exe" if os.name == "nt" else "agentic-workspace"
        )
        cls.project_kit = scripts / (
            "project-kit.exe" if os.name == "nt" else "project-kit"
        )
        subprocess.run(
            [str(cls.python), "-m", "ensurepip", "--upgrade"],
            check=True,
            text=True,
            capture_output=True,
        )
        install = [
            str(cls.python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            str(cls.wheel),
        ]
        subprocess.run(
            install,
            check=True,
            text=True,
            capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def _build(cls, output: Path):
        output.mkdir()
        source = cls.root / f"source-{output.name}"
        shutil.copytree(
            PRODUCT,
            source,
            ignore=shutil.ignore_patterns(
                "build",
                "dist",
                "*.egg-info",
                "__pycache__",
                "*.pyc",
                "graphify-out",
                ".squad",
                ".venv",
                ".git",
                "locks",
            ),
        )
        env = os.environ.copy()
        env["SOURCE_DATE_EPOCH"] = "1700000000"
        command = [
            sys.executable,
            "-m",
            "build",
            "--outdir",
            str(output),
        ]
        completed = subprocess.run(
            command,
            cwd=source,
            env=env,
            text=True,
            capture_output=True,
        )
        if completed.returncode:
            raise RuntimeError(
                "distribution build failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

    @staticmethod
    def _digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _sdist_contents(path: Path) -> dict[str, str]:
        contents = {}
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                relative = "/".join(PurePosixPath(member.name).parts[1:])
                extracted = archive.extractfile(member)
                assert extracted is not None
                contents[relative] = hashlib.sha256(extracted.read()).hexdigest()
        return contents

    def test_repeated_builds_have_reproducible_payloads(self):
        wheel_a = next(self.dist_a.glob("*.whl"))
        wheel_b = next(self.dist_b.glob("*.whl"))
        self.assertEqual(self._digest(wheel_a), self._digest(wheel_b))
        sdist_a = next(self.dist_a.glob("*.tar.gz"))
        sdist_b = next(self.dist_b.glob("*.tar.gz"))
        self.assertEqual(self._sdist_contents(sdist_a), self._sdist_contents(sdist_b))

    def test_archives_are_clean_and_contain_portable_launchers(self):
        with zipfile.ZipFile(self.wheel) as archive:
            wheel_names = archive.namelist()
        with tarfile.open(self.sdist, "r:gz") as archive:
            sdist_names = archive.getnames()

        expected_suffixes = (
            "agentic_workspace/project_kit_entry.py",
            "agentic_workspace/payload/agentic-workspace/spec-kit/bin/project-kit.py",
            "agentic_workspace/payload/agentic-workspace/extensions/data/README.md",
            "agentic_workspace/payload/agentic-workspace/extensions/software/README.md",
            "agentic_workspace/payload/agentic-workspace/extensions/software/docs/architecture-methods.md",
            "agentic_workspace/payload/agentic-workspace/extensions/software/docs/selection-guide.md",
            "agentic_workspace/payload/agentic-workspace/agents/software-architect.md",
            "agentic_workspace/payload/agentic-workspace/agents/project-developer.md",
            "agentic_workspace/payload/agentic-workspace/skills/develop-project/SKILL.md",
            "agentic_workspace/payload/agentic-workspace/skills/develop-project/agents/openai.yaml",
            "agentic_workspace/payload/agentic-workspace/skills/select-software-architecture/SKILL.md",
            "agentic_workspace/payload/agentic-workspace/skills/select-software-architecture/agents/openai.yaml",
            "agentic_workspace/payload/agentic-workspace/skills/select-software-architecture/references/decision-output.md",
            "agentic_workspace/payload/agentic-workspace/spec-kit/templates/software-architecture.md.tmpl",
            "agentic_workspace/payload/agentic-workspace/spec-kit/templates/remediation-control.md.tmpl",
        )
        for suffix in expected_suffixes:
            self.assertTrue(any(name.endswith(suffix) for name in wheel_names), suffix)
            self.assertTrue(any(name.endswith(suffix) for name in sdist_names), suffix)
        self.assertTrue(
            any(name.endswith("bin/agentic-workspace.py") for name in sdist_names)
        )

        for name in wheel_names + sdist_names:
            parts = PurePosixPath(name).parts
            self.assertNotIn("__pycache__", parts, name)
            self.assertNotIn("build", parts, name)
            self.assertNotIn("graphify-out", parts, name)
            self.assertNotIn(".squad", parts, name)
            self.assertNotIn(".venv", parts, name)
            self.assertFalse(name.endswith((".pyc", ".pyo")), name)

    def test_installed_wheel_installs_checks_and_creates_project(self):
        for command in (self.agentic_workspace, self.project_kit):
            result = subprocess.run(
                [str(command), "--help"], text=True, capture_output=True, check=True
            )
            self.assertIn("usage:", result.stdout.lower())

        repository = self.root / "installed-smoke"
        repository.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(repository)],
            text=True,
            capture_output=True,
            check=True,
        )
        install_result = subprocess.run(
            [str(self.agentic_workspace), "install", str(repository)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            0,
            install_result.returncode,
            f"install failed\nstdout:\n{install_result.stdout}\nstderr:\n{install_result.stderr}",
        )
        check_result = subprocess.run(
            [str(self.agentic_workspace), "check", str(repository)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            0,
            check_result.returncode,
            f"check failed\nstdout:\n{check_result.stdout}\nstderr:\n{check_result.stderr}",
        )

        guard = repository / "agentic-workspace/hooks/providers" / (
            "commit-message-guard.cmd" if os.name == "nt" else "commit-message-guard"
        )
        guard_command = (
            ["cmd.exe", "/d", "/c", str(guard)]
            if os.name == "nt"
            else [str(guard)]
        )
        clean = subprocess.run(
            guard_command,
            input=json.dumps({"tool_input": {"command": "git status"}}),
            cwd=repository,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, clean.returncode, clean.stderr)
        blocked = subprocess.run(
            guard_command,
            input=json.dumps(
                {
                    "tool_input": {
                        "command": "git commit -m x -m 'Co-Authored-By: A <a@example.com>'"
                    }
                }
            ),
            cwd=repository,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("BLOCKED", blocked.stderr)

        subprocess.run(
            [
                str(self.project_kit),
                "init",
                "portable-smoke",
                "--mode",
                "flexible",
                "--profile",
                "minimal",
                "--with",
                "software-architecture",
                "--with",
                "remediation-control",
            ],
            cwd=repository,
            text=True,
            capture_output=True,
            check=True,
        )
        project = repository / "agentic-workspace/projects/portable-smoke"
        self.assertTrue((project / "registry/project.json").is_file())
        self.assertTrue((project / "software-architecture.md").is_file())
        self.assertTrue((project / "remediation-control.md").is_file())
        installed_registry = json.loads(
            (project / "registry/project.json").read_text(encoding="utf-8")
        )
        self.assertIn("software-architecture", installed_registry["modules"])
        self.assertIn("remediation-control", installed_registry["modules"])
        subprocess.run(
            [str(self.project_kit), "validate", str(project), "--strict-index"],
            cwd=repository,
            text=True,
            capture_output=True,
            check=True,
        )

    def test_source_python_launchers_do_not_require_bash(self):
        commands = (
            [sys.executable, str(PRODUCT / "bin/agentic-workspace.py"), "--help"],
            [
                sys.executable,
                str(
                    PRODUCT
                    / "src/agentic_workspace/payload/agentic-workspace/spec-kit/bin/project-kit.py"
                ),
                "--help",
            ],
        )
        for command in commands:
            result = subprocess.run(
                command, cwd=PRODUCT, text=True, capture_output=True, check=True
            )
            self.assertIn("usage:", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
