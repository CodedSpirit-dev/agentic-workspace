from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


KIT = Path(__file__).resolve().parents[1]
CLI = KIT / "bin/project-kit"


class ProjectKitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, ok=True):
        result = subprocess.run(
            [str(CLI), *map(str, args)], text=True, capture_output=True, cwd=self.root
        )
        if ok and result.returncode:
            self.fail(
                f"command failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        if not ok and result.returncode == 0:
            self.fail(f"command unexpectedly passed: {args}")
        return result

    def init(self, profile="complex", mode="flexible"):
        self.run_cli(
            "init",
            "test-project",
            "--root",
            self.root,
            "--profile",
            profile,
            "--mode",
            mode,
        )
        return self.root / "test-project"

    def evidence(self, project, name="check.txt"):
        path = project / "evidence" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("observable evidence\n")
        return str(path.relative_to(project))

    def create_passed_verification(self, project, title="Acceptance"):
        evidence = self.evidence(project)
        self.run_cli(
            "create",
            project,
            "verification",
            "--title",
            title,
            "--status",
            "passed",
            "--method",
            "Automated regression command",
            "--evidence",
            evidence,
        )
        return "VER-001"

    def set_remediation_control(
        self,
        project,
        status,
        findings=("FND-001",),
        remediations=("TSK-001",),
        verifications=("VER-001",),
    ):
        path = project / "remediation-control.md"
        replacements = {
            "control_status": status,
            "finding_ids": json.dumps(list(findings)),
            "remediation_ids": json.dumps(list(remediations)),
            "verification_ids": json.dumps(list(verifications)),
        }
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            key = line.split(":", 1)[0]
            if key in replacements:
                lines[index] = f"{key}: {replacements[key]}"
        path.write_text("\n".join(lines) + "\n")

    def write_order_result(self, order_id="REPO-0001"):
        result_path = self.root / "result.json"
        result_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "order_id": order_id,
                    "status": "executed",
                    "execution": {"mode": "direct", "executed_by": "agent-a"},
                    "changes": [],
                    "validation": {
                        "status": "passed",
                        "checks": [{"method": "command", "result": "passed"}],
                    },
                    "evidence": ["evidence/check.txt"],
                }
            )
        )
        return result_path

    def test_profiles_share_registry_model(self):
        for profile in ("minimal", "standard", "complex"):
            name = f"{profile}-project"
            self.run_cli("init", name, "--root", self.root, "--profile", profile)
            registry = json.loads(
                (self.root / name / "registry/project.json").read_text()
            )
            self.assertEqual("2.1", registry["schema_version"])
            self.assertEqual(profile, registry["profile"])
            self.assertEqual("flexible", registry["mode"])
        self.assertFalse((self.root / "minimal-project/findings.md").exists())
        self.assertTrue((self.root / "standard-project/findings.md").exists())
        self.assertTrue((self.root / "complex-project/registry/agent-orders").exists())

    def test_modes_create_owned_cycle_directories(self):
        expected = {
            "traditional": ("phases", "PHS-001"),
            "sprint": ("sprints", "SPR-001"),
            "flexible": ("workstreams", "WST-001"),
        }
        for mode, (directory, cycle_id) in expected.items():
            name = f"{mode}-project"
            self.run_cli("init", name, "--root", self.root, "--mode", mode)
            project = self.root / name
            registry = json.loads((project / "registry/project.json").read_text())
            self.assertEqual(cycle_id, registry["cycles"][0]["id"])
            self.assertTrue((project / directory).is_dir())

    def test_cycle_requires_evidence_and_updates_status(self):
        project = self.init(mode="sprint")
        self.create_passed_verification(project)
        self.run_cli("cycle", "start", project, "SPR-001")
        self.run_cli("status", "update", project, "--state", "active", "--summary", "Sprint started.")
        self.run_cli("cycle", "close", project, "SPR-001", ok=False)
        self.run_cli(
            "cycle", "close", project, "SPR-001", "--evidence", "VER-001"
        )
        registry = json.loads((project / "registry/project.json").read_text())
        self.assertEqual("completed", registry["cycles"][0]["state"])
        self.assertFalse(registry["active_cycles"])
        self.assertIn("Sprint started", (project / "status.md").read_text())

    def test_cycle_rejects_unresolvable_or_escaping_evidence(self):
        project = self.init(mode="sprint")
        self.run_cli("cycle", "start", project, "SPR-001")
        result = self.run_cli(
            "cycle", "close", project, "SPR-001", "--evidence", "review done", ok=False
        )
        self.assertIn("does not resolve", result.stderr)
        result = self.run_cli(
            "cycle", "close", project, "SPR-001", "--evidence", "../outside.txt", ok=False
        )
        self.assertIn("escapes project", result.stderr)

    def test_sequential_modes_reject_parallel_active_cycles(self):
        project = self.init(mode="traditional")
        self.run_cli("cycle", "start", project, "PHS-001")
        self.run_cli("cycle", "create", project, "--title", "Delivery")
        result = self.run_cli("cycle", "start", project, "PHS-002", ok=False)
        self.assertIn("allows one active phase", result.stderr)

    def test_module_add_is_idempotent(self):
        project = self.init("minimal")
        self.run_cli("add-module", project, "metric-catalog")
        result = self.run_cli("add-module", project, "metric-catalog")
        self.assertIn("already enabled", result.stdout)
        registry = json.loads((project / "registry/project.json").read_text())
        self.assertEqual(1, registry["modules"].count("metric-catalog"))

    def test_software_architecture_module_is_opt_in_and_seeded(self):
        project = self.init("minimal")
        assessment = project / "software-architecture.md"
        self.assertFalse(assessment.exists())

        self.run_cli("add-module", project, "software-architecture")

        registry = json.loads((project / "registry/project.json").read_text())
        self.assertIn("software-architecture", registry["modules"])
        self.assertTrue(assessment.is_file())
        self.assertTrue((project / "registry/conventions").is_dir())
        assessment_text = assessment.read_text()
        self.assertIn("Feature-Sliced Design", assessment_text)
        self.assertIn("Software Architecture Assessment — Test Project", assessment_text)
        self.assertNotIn("{{", assessment_text)
        self.run_cli("validate", project, "--strict-index")

        assessment.write_text(
            assessment_text.replace("assessment_status: draft", "assessment_status: proposed")
        )
        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("proposed assessment requires source_ids", result.stdout)
        self.assertIn("proposed assessment requires decision_ids", result.stdout)

        self.run_cli("create", project, "requirement", "--title", "Change boundary")
        self.run_cli(
            "decision", "create", project, "--title", "Select architecture"
        )
        self.run_cli("relate", project, "DEC-001", "derived_from", "REQ-001")
        proposed_text = assessment.read_text().replace(
            "source_ids: []\ndecision_ids: []",
            'source_ids: ["REQ-001"]\ndecision_ids: ["DEC-001"]',
        )
        assessment.write_text(proposed_text)
        self.run_cli("validate", project, "--strict-index")

        self.run_cli("artifact", "set-status", project, "DEC-001", "rejected")
        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("DEC-001 must be draft for a proposed assessment", result.stdout)
        self.run_cli("artifact", "set-status", project, "DEC-001", "draft")
        self.run_cli("validate", project, "--strict-index")

        assessment.write_text(
            proposed_text.replace("assessment_status: proposed", "assessment_status: accepted")
        )
        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("accepted assessment requires convention_ids", result.stdout)
        self.assertIn("accepted assessment requires verification_ids", result.stdout)

        self.run_cli(
            "create", project, "convention", "--title", "Dependency direction", "--status", "active"
        )
        self.run_cli(
            "create", project, "verification", "--title", "Architecture checks", "--status", "active"
        )
        self.run_cli("artifact", "set-status", project, "DEC-001", "accepted")
        self.run_cli("relate", project, "CONV-001", "implements", "DEC-001")
        self.run_cli("relate", project, "VER-001", "verifies", "CONV-001")
        accepted_text = assessment.read_text()
        accepted_text = accepted_text.replace(
            "convention_ids: []", 'convention_ids: ["CONV-001"]'
        ).replace("verification_ids: []", 'verification_ids: ["VER-001"]')
        assessment.write_text(accepted_text)
        self.run_cli("validate", project, "--strict-index")

        registry_path = project / "registry/project.json"
        registry = json.loads(registry_path.read_text())
        registry["relations"] = [
            relation
            for relation in registry["relations"]
            if relation
            not in (
                {"source": "CONV-001", "type": "implements", "target": "DEC-001"},
                {"source": "VER-001", "type": "verifies", "target": "CONV-001"},
            )
        ]
        registry["relations"].extend(
            [
                {"source": "CONV-001", "type": "related", "target": "VER-001"},
                {"source": "VER-001", "type": "related", "target": "CONV-001"},
            ]
        )
        registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
        self.run_cli("index", project)
        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("CONV-001 must connect to a listed decision", result.stdout)
        self.assertIn("VER-001 must connect to a listed decision", result.stdout)

        self.run_cli(
            "init",
            "software-project",
            "--root",
            self.root,
            "--profile",
            "minimal",
            "--with",
            "software-architecture",
        )
        initialized = self.root / "software-project"
        enabled = json.loads((initialized / "registry/project.json").read_text())
        self.assertIn("software-architecture", enabled["modules"])
        self.assertTrue((initialized / "software-architecture.md").is_file())

    def test_remediation_control_is_opt_in_and_validates_active_graph(self):
        project = self.init("minimal")
        self.assertFalse((project / "remediation-control.md").exists())
        self.run_cli("add-module", project, "remediation-control")
        self.assertTrue((project / "remediation-control.md").is_file())
        self.run_cli("validate", project, "--strict-index")

        self.run_cli(
            "create", project, "finding", "--title", "Observed gap", "--status", "confirmed"
        )
        self.run_cli("create", project, "task", "--title", "Repair gap", "--status", "ready")
        self.run_cli(
            "create", project, "verification", "--title", "Acceptance", "--status", "active"
        )
        self.set_remediation_control(project, "active")

        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("TSK-001 must reach a listed finding", result.stdout)
        self.assertIn("FND-001 is not addressed", result.stdout)
        self.assertIn("TSK-001 lacks a listed verification", result.stdout)

        self.run_cli("relate", project, "TSK-001", "addresses", "FND-001")
        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("TSK-001 lacks a listed verification", result.stdout)
        self.run_cli("relate", project, "VER-001", "verifies", "TSK-001")
        self.run_cli("validate", project, "--strict-index")
        result = self.run_cli(
            "status", "update", project, "--state", "completed",
            "--summary", "Premature completion", ok=False,
        )
        self.assertIn("remediation-control is not completed", result.stderr)

    def test_remediation_control_rejects_wrong_types_and_isolated_cycles(self):
        project = self.init("minimal")
        self.run_cli("add-module", project, "remediation-control")
        self.run_cli(
            "create", project, "finding", "--title", "Observed gap", "--status", "confirmed"
        )
        for title in ("First repair", "Second repair"):
            self.run_cli("create", project, "task", "--title", title, "--status", "ready")
        for title in ("First acceptance", "Second acceptance"):
            self.run_cli(
                "create", project, "verification", "--title", title, "--status", "active"
            )
        self.set_remediation_control(
            project,
            "active",
            remediations=("TSK-001", "TSK-002"),
            verifications=("VER-001", "VER-002"),
        )
        self.run_cli("relate", project, "TSK-001", "addresses", "TSK-002")
        self.run_cli("relate", project, "TSK-002", "addresses", "TSK-001")
        self.run_cli("relate", project, "VER-001", "verifies", "TSK-001")
        self.run_cli("relate", project, "VER-002", "verifies", "TSK-002")

        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("TSK-001 must reach a listed finding", result.stdout)
        self.assertIn("TSK-002 must reach a listed finding", result.stdout)
        self.assertIn("FND-001 is not addressed", result.stdout)

        self.set_remediation_control(
            project,
            "active",
            findings=("TSK-001",),
            remediations=("FND-001",),
            verifications=("VER-001",),
        )
        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("TSK-001 must be type finding", result.stdout)
        self.assertIn("FND-001 must be type decision or risk or task", result.stdout)

    def test_remediation_control_completed_requires_terminal_evidence(self):
        project = self.init("minimal")
        self.run_cli("add-module", project, "remediation-control")
        self.run_cli(
            "create", project, "finding", "--title", "Observed gap", "--status", "confirmed"
        )
        self.run_cli("create", project, "task", "--title", "Repair gap", "--status", "ready")
        self.run_cli(
            "create", project, "verification", "--title", "Acceptance", "--status", "active"
        )
        self.run_cli("relate", project, "TSK-001", "addresses", "FND-001")
        self.run_cli("relate", project, "VER-001", "verifies", "TSK-001")
        self.set_remediation_control(project, "completed")

        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("requires FND-001 to be", result.stdout)
        self.assertIn("requires TSK-001 to be done", result.stdout)
        self.assertIn("requires VER-001 to be passed", result.stdout)

        self.run_cli("artifact", "set-status", project, "FND-001", "resolved")
        self.run_cli("artifact", "set-status", project, "TSK-001", "done")
        evidence = self.evidence(project)
        self.run_cli(
            "artifact", "set-status", project, "VER-001", "passed",
            "--method", "Automated regression", "--evidence", evidence,
        )
        self.run_cli("validate", project, "--strict-index")

    def test_stable_ids_gaps_and_duplicate_rejection(self):
        project = self.init()
        self.run_cli("create", project, "exploration", "--title", "First")
        self.run_cli("create", project, "exploration", "--title", "Gap", "--id", "EXP-010")
        self.run_cli("create", project, "exploration", "--title", "Second")
        registry = json.loads((project / "registry/project.json").read_text())
        self.assertEqual(
            ["EXP-001", "EXP-010", "EXP-002"],
            [artifact["id"] for artifact in registry["artifacts"]],
        )
        self.run_cli(
            "create", project, "finding", "--title", "Duplicate", "--id", "EXP-001", ok=False
        )

    def test_relations_validate_missing_reference(self):
        project = self.init()
        self.run_cli("create", project, "exploration", "--title", "Source")
        self.run_cli("create", project, "finding", "--title", "Finding", "--status", "confirmed")
        self.run_cli("relate", project, "EXP-001", "produces", "FND-001")
        self.run_cli("validate", project, "--strict-index")
        registry_path = project / "registry/project.json"
        registry = json.loads(registry_path.read_text())
        registry["relations"][0]["target"] = "FND-999"
        registry_path.write_text(json.dumps(registry))
        result = self.run_cli("validate", project, ok=False)
        self.assertIn("relation target missing", result.stdout)

    def test_deliverable_acceptance_requires_requirement_and_verification(self):
        project = self.init()
        self.run_cli("create", project, "requirement", "--title", "Required outcome")
        self.run_cli("create", project, "deliverable", "--title", "Release package")
        result = self.run_cli(
            "artifact", "set-status", project, "DEL-001", "accepted", ok=False
        )
        self.assertIn("lacks a requirement relation", result.stderr)
        self.assertIn("lacks a passed verification relation", result.stderr)
        self.create_passed_verification(project)
        self.run_cli("relate", project, "DEL-001", "addresses", "REQ-001")
        self.run_cli("relate", project, "VER-001", "verifies", "DEL-001")
        self.run_cli("artifact", "set-status", project, "DEL-001", "accepted")
        self.run_cli("validate", project, "--strict-index")

    def test_passed_verification_requires_method_and_resolvable_evidence(self):
        project = self.init()
        result = self.run_cli(
            "create", project, "verification", "--title", "Unsafe pass", "--status", "passed", ok=False
        )
        self.assertIn("requires --method", result.stderr)
        self.assertFalse((project / "verifications/ver-001-unsafe-pass.md").exists())
        self.run_cli("create", project, "verification", "--title", "Check")
        result = self.run_cli(
            "artifact", "set-status", project, "VER-001", "passed",
            "--method", "Manual review", "--evidence", "missing.txt", ok=False,
        )
        self.assertIn("does not resolve", result.stderr)
        evidence = self.evidence(project)
        self.run_cli(
            "artifact", "set-status", project, "VER-001", "passed",
            "--method", "Manual review", "--evidence", evidence,
        )
        self.run_cli("validate", project)

    def test_order_claim_conflict_and_release(self):
        project = self.init()
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Test order",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        self.run_cli("order", "ready", project, "REPO-0001")
        self.run_cli("order", "claim", project, "REPO-0001", "--agent", "agent-a")
        result = self.run_cli(
            "order", "claim", project, "REPO-0001", "--agent", "agent-b", ok=False
        )
        self.assertIn("already claimed", result.stderr)
        self.run_cli("order", "release", project, "REPO-0001", "--agent", "agent-a")
        self.run_cli("order", "claim", project, "REPO-0001", "--agent", "agent-b")

    def test_recover_expired_never_steals_live_lease(self):
        project = self.init()
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Lease",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        self.run_cli("order", "ready", project, "REPO-0001")
        self.run_cli("order", "claim", project, "REPO-0001", "--agent", "agent-a")
        result = self.run_cli(
            "order", "claim", project, "REPO-0001", "--agent", "agent-b",
            "--recover-expired", ok=False,
        )
        self.assertIn("already claimed by agent-a", result.stderr)
        context_path = next((project / "registry/agent-orders").glob("*/context.json"))
        context = json.loads(context_path.read_text())
        context["claim"]["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        context_path.write_text(json.dumps(context))
        result = self.run_cli(
            "order", "claim", project, "REPO-0001", "--agent", "agent-b", ok=False
        )
        self.assertIn("pass --recover-expired", result.stderr)
        self.run_cli(
            "order", "claim", project, "REPO-0001", "--agent", "agent-b",
            "--recover-expired",
        )

    def test_order_cannot_close_without_result_and_verification(self):
        project = self.init()
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Close gate",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        self.run_cli("order", "ready", project, "REPO-0001")
        self.run_cli("order", "start", project, "REPO-0001")
        self.run_cli("order", "close", project, "REPO-0001", ok=False)

    def test_order_result_verify_and_close(self):
        project = self.init()
        self.create_passed_verification(project, "Order verification")
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Execute change",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        self.run_cli("order", "ready", project, "REPO-0001")
        self.run_cli("order", "start", project, "REPO-0001")
        result_path = self.write_order_result()
        self.run_cli("order", "record-result", project, "REPO-0001", "--result", result_path)
        self.run_cli("order", "verify", project, "REPO-0001", "--verification", "VER-001")
        self.run_cli("order", "close", project, "REPO-0001")
        self.run_cli("validate", project, "--strict-index")

    def test_order_result_contract_is_fully_enforced(self):
        project = self.init()
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Contract",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        self.run_cli("order", "ready", project, "REPO-0001")
        self.run_cli("order", "start", project, "REPO-0001")
        invalid = self.root / "invalid-result.json"
        invalid.write_text(json.dumps({"schema_version": "1.0", "order_id": "REPO-0001"}))
        result = self.run_cli(
            "order", "record-result", project, "REPO-0001", "--result", invalid, ok=False
        )
        self.assertIn("missing required property 'status'", result.stderr)
        self.assertFalse(next((project / "registry/agent-orders").glob("*/result.json"), None))
        malformed = self.write_order_result()
        data = json.loads(malformed.read_text())
        data["unexpected"] = True
        malformed.write_text(json.dumps(data))
        result = self.run_cli(
            "order", "record-result", project, "REPO-0001", "--result", malformed, ok=False
        )
        self.assertIn("additional property 'unexpected'", result.stderr)

        for field, invalid_value, expected_error in (
            ("mode", 123, "execution.mode: expected one of"),
            ("executed_by", [], "execution.executed_by: expected type string"),
            ("executed_by", "", "execution.executed_by: string is shorter than minLength"),
        ):
            malformed = self.write_order_result()
            data = json.loads(malformed.read_text())
            data["execution"][field] = invalid_value
            malformed.write_text(json.dumps(data))
            result = self.run_cli(
                "order",
                "record-result",
                project,
                "REPO-0001",
                "--result",
                malformed,
                ok=False,
            )
            self.assertIn(expected_error, result.stderr)

        context_path = next((project / "registry/agent-orders").glob("*/context.json"))
        context = json.loads(context_path.read_text())
        self.assertEqual("in_progress", context["status"])
        self.assertFalse(next((project / "registry/agent-orders").glob("*/result.json"), None))

    def test_order_markdown_divergence_is_detected(self):
        project = self.init()
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Divergence",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        order_md = next((project / "registry/agent-orders").glob("*/order.md"))
        order_md.write_text(order_md.read_text() + "\nmanual divergence\n")
        result = self.run_cli("validate", project, ok=False)
        self.assertIn("diverged", result.stdout)

    def test_secret_pattern_is_rejected(self):
        project = self.init()
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Secret",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        context_path = next((project / "registry/agent-orders").glob("*/context.json"))
        context = json.loads(context_path.read_text())
        context["background"] = "password: actual-secret"
        context_path.write_text(json.dumps(context))
        result = self.run_cli("validate", project, ok=False)
        self.assertIn("may contain a secret", result.stdout)

    def test_migration_dry_run_does_not_change_project(self):
        project = self.root / "legacy-project"
        project.mkdir()
        (project / "index.md").write_text("# Legacy\n")
        self.run_cli("migrate", project, "--dry-run")
        self.assertFalse((project / "registry").exists())

    def test_migration_apply_seeds_a_valid_project(self):
        project = self.root / "legacy-project"
        project.mkdir()
        (project / "legacy-notes.md").write_text("# Legacy\n")
        self.run_cli("migrate", project, "--apply")
        self.run_cli("validate", project, "--strict-index")
        self.assertTrue((project / "charter.md").is_file())
        self.assertTrue((project / "tasks.md").is_file())
        self.assertTrue((project / "registry/risks").is_dir())

    def test_stale_index_and_status_are_detected_and_regenerated(self):
        project = self.init()
        self.run_cli("create", project, "finding", "--title", "Indexed", "--status", "confirmed")
        (project / "registry/index.md").write_text("stale\n")
        (project / "status.md").write_text("stale\n")
        result = self.run_cli("validate", project, "--strict-index", ok=False)
        self.assertIn("registry index is stale", result.stdout)
        self.assertIn("status view is stale", result.stdout)
        self.assertEqual("stale\n", (project / "registry/index.md").read_text())
        self.assertEqual("stale\n", (project / "status.md").read_text())
        self.run_cli("index", project)
        self.run_cli("validate", project, "--strict-index")

    def test_validate_and_audit_are_read_only(self):
        project = self.init()
        order_md = None
        self.run_cli(
            "order", "create", project, "--domain", "repo", "--title", "Read only",
            "--scope", "Fixture", "--out-of-scope", "Production",
        )
        order_md = next((project / "registry/agent-orders").glob("*/order.md"))
        order_md.write_text(order_md.read_text() + "\nmanual divergence\n")
        (project / "registry/index.md").write_text("stale\n")
        before = {path.relative_to(project): path.read_bytes() for path in project.rglob("*") if path.is_file()}
        self.run_cli("validate", project, "--strict-index", ok=False)
        self.run_cli("audit", project, ok=False)
        after = {path.relative_to(project): path.read_bytes() for path in project.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((project / "registry/audit-report.md").exists())

    def test_project_completion_requires_terminal_cycles_risks_and_deliverables(self):
        project = self.init()
        result = self.run_cli(
            "status", "update", project, "--state", "completed", "--summary", "Done", ok=False
        )
        self.assertIn("non-terminal cycles remain", result.stderr)
        self.run_cli("create", project, "risk", "--title", "Open risk")
        self.run_cli("create", project, "requirement", "--title", "Required")
        self.run_cli("create", project, "deliverable", "--title", "Package")
        self.create_passed_verification(project)
        self.run_cli("relate", project, "DEL-001", "addresses", "REQ-001")
        self.run_cli("relate", project, "VER-001", "verifies", "DEL-001")
        self.run_cli("cycle", "start", project, "WST-001")
        self.run_cli("cycle", "close", project, "WST-001", "--evidence", "VER-001")
        result = self.run_cli(
            "status", "update", project, "--state", "completed", "--summary", "Done", ok=False
        )
        self.assertIn("undisposed risks", result.stderr)
        self.assertIn("unaccepted deliverables", result.stderr)
        self.run_cli("artifact", "set-status", project, "RSK-001", "accepted")
        self.run_cli("artifact", "set-status", project, "DEL-001", "accepted")
        self.run_cli(
            "status", "update", project, "--state", "completed", "--summary", "Done"
        )
        self.run_cli("validate", project, "--strict-index")


if __name__ == "__main__":
    unittest.main()
