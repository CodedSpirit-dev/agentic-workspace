#!/usr/bin/env python3
"""Deterministic CLI for portable project registries, cycles, and agent orders."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


KIT = Path(__file__).resolve().parents[1]
MODEL = json.loads((KIT / "config/model.json").read_text(encoding="utf-8"))
ORDER_RESULT_SCHEMA = json.loads(
    (KIT / "schemas/order-result.schema.json").read_text(encoding="utf-8")
)
ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*-[0-9]{3,}$")
ORDER_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*-[0-9]{4,}$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECRET_RE = re.compile(
    r"(?i)(?:\b(password|passwd|token|api[_-]?key|cookie|pat)\b\s*[:=]\s*(\S+)|authorization\s*:\s*bearer\s+\S+)"
)


class KitError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def today() -> str:
    return datetime.now().date().isoformat()


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not text:
        raise KitError("title cannot produce an empty kebab-case slug")
    return text


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KitError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise KitError(f"invalid JSON in {path}: {exc}") from exc


def contains_secret(value: object) -> bool:
    sensitive = {"password", "passwd", "token", "api_key", "api-key", "cookie", "pat"}
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower()
            if normalized in sensitive and item not in (None, "", []):
                text = str(item)
                if not re.fullmatch(r"\$?\{?[A-Z][A-Z0-9_]*\}?", text):
                    return True
            if contains_secret(item):
                return True
        return False
    if isinstance(value, list):
        return any(contains_secret(item) for item in value)
    if isinstance(value, str):
        match = SECRET_RE.search(value)
        if not match:
            return False
        candidate = (match.group(2) or "").strip("\"'{}")
        return not candidate or not re.fullmatch(r"\$?[A-Z][A-Z0-9_]*", candidate)
    return False


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _json_type_matches(value: object, expected: str) -> bool:
    """Return whether value has a JSON type (where bool is not an integer)."""
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: isinstance(value, (int, float))
        and not isinstance(value, bool),
        "boolean": lambda: isinstance(value, bool),
        "null": lambda: value is None,
    }.get(expected, lambda: False)()


def validate_json_schema(
    value: object, schema: dict, location: str = "$"
) -> list[str]:
    """Validate the JSON Schema keywords used by the portable contracts.

    This intentionally small stdlib validator keeps the CLI dependency-free. It
    rejects unknown schema keywords instead of silently claiming validation.
    """
    supported = {
        "$schema",
        "$id",
        "title",
        "description",
        "type",
        "required",
        "properties",
        "additionalProperties",
        "items",
        "enum",
        "const",
        "pattern",
        "minLength",
        "minItems",
        "uniqueItems",
    }
    unknown = set(schema) - supported
    if unknown:
        return [f"{location}: unsupported schema keyword(s): {', '.join(sorted(unknown))}"]

    errors: list[str] = []
    expected_types = schema.get("type")
    if expected_types is not None:
        choices = [expected_types] if isinstance(expected_types, str) else expected_types
        if not any(_json_type_matches(value, item) for item in choices):
            errors.append(f"{location}: expected type {' or '.join(choices)}")
            return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: expected one of {schema['enum']!r}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{location}: string is shorter than minLength")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(f"{location}: does not match required pattern")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{location}: array is shorter than minItems")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{location}: array items must be unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_json_schema(item, item_schema, f"{location}[{index}]"))
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{location}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors.extend(
                    validate_json_schema(item, properties[key], f"{location}.{key}")
                )
            elif schema.get("additionalProperties") is False:
                errors.append(f"{location}: additional property {key!r} is not allowed")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors.extend(
                    validate_json_schema(
                        item, schema["additionalProperties"], f"{location}.{key}"
                    )
                )
    return errors


def validate_order_result(data: object, expected_order_id: str | None = None) -> list[str]:
    errors = validate_json_schema(data, ORDER_RESULT_SCHEMA, "result")
    if isinstance(data, dict) and expected_order_id is not None:
        if data.get("order_id") != expected_order_id:
            errors.append(
                f"result.order_id: expected {expected_order_id!r}, got {data.get('order_id')!r}"
            )
    if contains_secret(data):
        errors.append("result may contain a secret")
    return errors


@contextmanager
def registry_lock(project: Path):
    lock = project / "registry/.registry.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise KitError(
            f"registry is locked: {lock}; inspect and remove only if stale"
        ) from exc
    try:
        os.write(fd, f"pid={os.getpid()} at={now()}\n".encode())
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def registry_path(project: Path) -> Path:
    return project / "registry/project.json"


def load_registry(project: Path) -> dict:
    return read_json(registry_path(project))


def save_registry(project: Path, registry: dict) -> None:
    registry["updated_at"] = now()
    write_json(registry_path(project), registry)


def project_arg(value: str) -> Path:
    return Path(value).expanduser().resolve()


def render_template(name: str, values: dict[str, str]) -> str:
    text = (KIT / "templates" / name).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def seed_file(path: Path, title: str) -> None:
    template = KIT / "templates/v2" / f"{path.name}.tmpl"
    if not template.exists():
        template = KIT / "templates" / f"{path.name}.tmpl"
    if template.exists():
        text = template.read_text(encoding="utf-8")
        replacements = {
            "{{PROJECT_NAME}}": title,
            "{{PROJECT_TITLE}}": title.replace("-", " ").title(),
            "{{DATE}}": today(),
            "{PROJECT_TITLE}": title.replace("-", " ").title(),
            "{project_name}": title,
            "{YYYY-MM-DD}": today(),
            "{planned | active | blocked | at-risk | completed | archived}": "planned",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
    else:
        text = f"# {title}: {path.stem.replace('-', ' ').title()}\n\n(TODO: confirm)\n"
    path.write_text(text, encoding="utf-8")


def add_module(project: Path, module: str, registry: dict | None = None) -> bool:
    if module not in MODEL["modules"]:
        raise KitError(
            f"unknown module {module!r}; choose from {', '.join(MODEL['modules'])}"
        )
    registry = registry or load_registry(project)
    if module in registry["modules"]:
        return False
    spec = MODEL["modules"][module]
    for rel in spec["directories"]:
        directory = project / rel
        directory.mkdir(parents=True, exist_ok=True)
    for rel in spec["files"]:
        path = project / rel
        if not path.exists():
            seed_file(path, registry["project"])
    registry["modules"].append(module)
    registry["modules"].sort()
    return True


def cycle_spec(registry: dict) -> dict:
    mode = registry.get("mode")
    spec = MODEL["project_modes"].get(mode)
    if not spec:
        raise KitError(f"unknown project mode: {mode!r}")
    return spec


def create_cycle(project: Path, registry: dict, title: str) -> dict:
    spec = cycle_spec(registry)
    prefix = spec["prefix"]
    current = registry["counters"].get(prefix, 0) + 1
    registry["counters"][prefix] = current
    cycle_id = f"{prefix}-{current:03d}"
    relpath = str(
        Path(spec["directory"]) / f"{cycle_id.lower()}-{slug(title)}.md"
    )
    path = project / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    text = render_template(
        "cycle.md.tmpl",
        {
            "id": cycle_id,
            "label": spec["cycle_label"],
            "title": title,
            "state": "planned",
            "date": today(),
        },
    )
    path.write_text(text, encoding="utf-8")
    cycle = {
        "id": cycle_id,
        "title": title,
        "state": "planned",
        "path": relpath,
        "created_at": now(),
        "updated_at": now(),
        "closure_evidence": [],
    }
    registry["cycles"].append(cycle)
    return cycle


def find_cycle(registry: dict, cycle_id: str) -> dict:
    matches = [cycle for cycle in registry.get("cycles", []) if cycle["id"] == cycle_id]
    if len(matches) != 1:
        raise KitError(f"expected one cycle for {cycle_id}, found {len(matches)}")
    return matches[0]


def render_status(project: Path, registry: dict) -> str:
    spec = cycle_spec(registry)
    rows = [
        f"# {registry['project']}: Status",
        "",
        "> Generated from `registry/project.json`; do not edit manually.",
        "",
        f"- **Mode:** {registry['mode']}",
        f"- **State:** {registry['state']}",
        f"- **Active {spec['cycle_label']} IDs:** "
        + (", ".join(f"`{value}`" for value in registry.get("active_cycles", [])) or "None"),
        "",
        "## History",
        "",
        "| At | State | Summary |",
        "|---|---|---|",
    ]
    for item in registry.get("status_history", []):
        summary = str(item.get("summary", "")).replace("|", "\\|")
        rows.append(f"| {item.get('at', '')} | {item.get('state', '')} | {summary} |")
    return "\n".join(rows) + "\n"


def evidence_reference_errors(
    project: Path, registry: dict, references: list[str], subject: str
) -> list[str]:
    """Require evidence to resolve to a registered artifact or in-project file."""
    known = {
        value
        for artifact in registry.get("artifacts", [])
        for value in [artifact.get("id"), *artifact.get("aliases", [])]
        if value
    }
    errors: list[str] = []
    for reference in references:
        if reference == subject:
            errors.append(f"{subject} cannot use itself as evidence")
            continue
        if reference in known:
            continue
        candidate = Path(reference)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (project / candidate).resolve()
        try:
            resolved.relative_to(project.resolve())
        except ValueError:
            errors.append(f"{subject} evidence escapes project: {reference}")
            continue
        if not resolved.is_file():
            errors.append(f"{subject} evidence does not resolve: {reference}")
    return errors


def project_completion_errors(project: Path, registry: dict) -> list[str]:
    errors: list[str] = []
    nonterminal_cycles = [
        cycle["id"]
        for cycle in registry.get("cycles", [])
        if cycle.get("state") not in {"completed", "cancelled"}
    ]
    if nonterminal_cycles:
        errors.append(
            "non-terminal cycles remain: " + ", ".join(nonterminal_cycles)
        )
    open_risks = [
        artifact["id"]
        for artifact in registry.get("artifacts", [])
        if artifact.get("type") == "risk"
        and artifact.get("status") not in {"mitigated", "accepted", "closed", "archived"}
    ]
    if open_risks:
        errors.append("undisposed risks remain: " + ", ".join(open_risks))
    pending_deliverables = [
        artifact["id"]
        for artifact in registry.get("artifacts", [])
        if artifact.get("type") == "deliverable"
        and artifact.get("status") not in {"accepted", "superseded", "archived"}
    ]
    if pending_deliverables:
        errors.append(
            "unaccepted deliverables remain: " + ", ".join(pending_deliverables)
        )
    return errors


def deliverable_gate_errors(project: Path, registry: dict, artifact: dict) -> list[str]:
    errors: list[str] = []
    requirement_links = [
        relation
        for relation in registry.get("relations", [])
        if relation.get("source") == artifact.get("id")
        and relation.get("type") in {"addresses", "implements"}
        and any(
            candidate.get("id") == relation.get("target")
            and candidate.get("type") == "requirement"
            for candidate in registry.get("artifacts", [])
        )
    ]
    passed_verifications = [
        candidate
        for relation in registry.get("relations", [])
        for candidate in registry.get("artifacts", [])
        if relation.get("target") == artifact.get("id")
        and relation.get("type") == "verifies"
        and candidate.get("id") == relation.get("source")
        and candidate.get("type") == "verification"
        and candidate.get("status") == "passed"
    ]
    if not requirement_links:
        errors.append(f"{artifact['id']} lacks a requirement relation")
    if not passed_verifications:
        errors.append(f"{artifact['id']} lacks a passed verification relation")
    for verification in passed_verifications:
        if not verification.get("verification_method"):
            errors.append(f"{verification['id']} passed without verification method")
        if not verification.get("evidence_refs"):
            errors.append(f"{verification['id']} passed without evidence")
        else:
            errors.extend(
                evidence_reference_errors(
                    project,
                    registry,
                    verification["evidence_refs"],
                    verification["id"],
                )
            )
    return errors


def cmd_init(args: argparse.Namespace) -> None:
    if not KEBAB_RE.fullmatch(args.name):
        raise KitError("project name must be descriptive kebab-case")
    root = Path(args.root).expanduser().resolve()
    project = root / args.name
    if project.exists() and any(project.iterdir()):
        raise KitError(f"project already exists and is not empty: {project}")
    project.mkdir(parents=True, exist_ok=True)
    registry = {
        "schema_version": "2.1",
        "project": args.name,
        "profile": args.profile,
        "mode": args.mode,
        "state": "planned",
        "created_at": now(),
        "updated_at": now(),
        "modules": [],
        "counters": {},
        "artifacts": [],
        "relations": [],
        "cycles": [],
        "active_cycles": [],
        "status_history": [
            {"at": now(), "state": "planned", "summary": "Project initialized."}
        ],
    }
    requested = list(MODEL["profiles"][args.profile]) + list(args.with_modules or [])
    for module in dict.fromkeys(requested):
        add_module(project, module, registry)
    first_titles = {
        "traditional": "Initiation phase",
        "sprint": "Foundation sprint",
        "flexible": "Foundation workstream",
    }
    create_cycle(project, registry, first_titles[args.mode])
    save_registry(project, registry)
    generate_indexes(project)
    print(project)


def cmd_add_module(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        changed = add_module(project, args.module, registry)
        save_registry(project, registry)
    generate_indexes(project)
    print("added" if changed else "already enabled")


def cmd_cycle_create(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        cycle = create_cycle(project, registry, args.title)
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{cycle['id']} {project / cycle['path']}")


def cmd_cycle_list(args: argparse.Namespace) -> None:
    registry = load_registry(project_arg(args.project))
    for cycle in registry.get("cycles", []):
        print(f"{cycle['id']}\t{cycle['state']}\t{cycle['title']}\t{cycle['path']}")


def cmd_cycle_start(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        cycle = find_cycle(registry, args.id)
        if cycle["state"] not in {"planned", "blocked"}:
            raise KitError(f"cannot start cycle {args.id} from {cycle['state']}")
        spec = cycle_spec(registry)
        other_active = [value for value in registry.get("active_cycles", []) if value != args.id]
        if other_active and not spec["parallel"]:
            raise KitError(
                f"{registry['mode']} mode allows one active {spec['cycle_label']}; "
                f"close {other_active[0]} first"
            )
        cycle["state"] = "active"
        cycle["updated_at"] = now()
        if args.id not in registry["active_cycles"]:
            registry["active_cycles"].append(args.id)
        if registry["state"] == "planned":
            registry["state"] = "active"
            registry["status_history"].append(
                {"at": now(), "state": "active", "summary": f"Started {args.id}."}
            )
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{args.id} active")


def cmd_cycle_close(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        cycle = find_cycle(registry, args.id)
        if cycle["state"] not in {"active", "blocked"}:
            raise KitError(f"cannot close cycle {args.id} from {cycle['state']}")
        if not args.evidence:
            raise KitError("cycle closure requires at least one --evidence value")
        evidence_errors = evidence_reference_errors(
            project, registry, list(args.evidence), args.id
        )
        if evidence_errors:
            raise KitError("; ".join(evidence_errors))
        cycle["state"] = "completed"
        cycle["updated_at"] = now()
        cycle["closure_evidence"] = list(args.evidence)
        registry["active_cycles"] = [
            value for value in registry.get("active_cycles", []) if value != args.id
        ]
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{args.id} completed")


def cmd_status_update(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        if args.state not in MODEL["project_states"]:
            raise KitError(f"invalid project state: {args.state}")
        if args.state == "completed":
            integrity_errors = validate_project(project, strict_index=True)
            if integrity_errors:
                raise KitError(
                    "cannot complete an invalid project: "
                    + "; ".join(integrity_errors)
                )
            completion_errors = project_completion_errors(project, registry)
            if completion_errors:
                raise KitError(
                    "cannot complete project: " + "; ".join(completion_errors)
                )
        registry["state"] = args.state
        registry.setdefault("status_history", []).append(
            {"at": now(), "state": args.state, "summary": args.summary}
        )
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{args.state}: {args.summary}")


def cmd_status_show(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    registry = load_registry(project)
    print(render_status(project, registry), end="")


def cmd_artifact_status(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        artifact = find_artifact(registry, args.id)
        states = MODEL["artifact_types"][artifact["type"]]["states"]
        if args.state not in states:
            raise KitError(
                f"invalid status {args.state!r} for {artifact['type']}; choose from {', '.join(states)}"
            )
        if artifact["type"] == "verification" and args.state == "passed":
            method = args.method or artifact.get("verification_method")
            evidence_refs = list(args.evidence or artifact.get("evidence_refs", []))
            if not method:
                raise KitError("passed verification requires --method")
            if not evidence_refs:
                raise KitError("passed verification requires at least one --evidence")
            evidence_errors = evidence_reference_errors(
                project, registry, evidence_refs, artifact["id"]
            )
            if evidence_errors:
                raise KitError("; ".join(evidence_errors))
            artifact["verification_method"] = method
            artifact["evidence_refs"] = evidence_refs
        if artifact["type"] == "deliverable" and args.state in {
            "verified",
            "accepted",
        }:
            gate_errors = deliverable_gate_errors(project, registry, artifact)
            if gate_errors:
                raise KitError("; ".join(gate_errors))
        artifact["status"] = args.state
        artifact["updated_at"] = today()
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{artifact['id']} {args.state}")


def next_id(
    registry: dict, artifact_type: str, prefix: str | None = None, width: int = 3
) -> str:
    if artifact_type not in MODEL["artifact_types"]:
        raise KitError(f"unknown artifact type: {artifact_type}")
    prefix = prefix or MODEL["artifact_types"][artifact_type]["prefix"]
    current = registry["counters"].get(prefix, 0)
    used = {a["id"] for a in registry["artifacts"]}
    while True:
        current += 1
        candidate = f"{prefix}-{current:0{width}d}"
        if candidate not in used:
            registry["counters"][prefix] = current
            return candidate


def find_artifact(registry: dict, artifact_id: str) -> dict:
    matches = [
        a
        for a in registry["artifacts"]
        if a["id"] == artifact_id or artifact_id in a.get("aliases", [])
    ]
    if len(matches) != 1:
        raise KitError(f"expected one artifact for {artifact_id}, found {len(matches)}")
    return matches[0]


def cmd_create(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        spec = MODEL["artifact_types"].get(args.type)
        if not spec:
            raise KitError(f"unknown artifact type: {args.type}")
        status = args.status or spec["states"][0]
        if status not in spec["states"]:
            raise KitError(f"invalid status {status!r} for {args.type}")
        method = getattr(args, "method", None)
        evidence_refs = list(getattr(args, "evidence", None) or [])
        if args.type != "verification" and (method or evidence_refs):
            raise KitError("--method and --evidence apply only to verification artifacts")
        artifact_id = args.id or next_id(registry, args.type)
        if not ID_RE.fullmatch(artifact_id):
            raise KitError(f"invalid artifact ID: {artifact_id}")
        if any(
            artifact_id == a["id"] or artifact_id in a.get("aliases", [])
            for a in registry["artifacts"]
        ):
            raise KitError(f"duplicate artifact ID or alias: {artifact_id}")
        if args.type == "verification" and status == "passed":
            if not method:
                raise KitError("passed verification requires --method")
            if not evidence_refs:
                raise KitError(
                    "passed verification requires at least one --evidence"
                )
            evidence_errors = evidence_reference_errors(
                project, registry, evidence_refs, artifact_id
            )
            if evidence_errors:
                raise KitError("; ".join(evidence_errors))
        directory = project / spec["directory"]
        directory.mkdir(parents=True, exist_ok=True)
        relpath = str(
            (Path(spec["directory"]) / f"{artifact_id.lower()}-{slug(args.title)}.md")
        ).lstrip("./")
        path = project / relpath
        path.write_text(
            render_template(
                "artifact.md.tmpl",
                {
                    "id": artifact_id,
                    "type": args.type,
                    "title": args.title,
                    "status": status,
                    "date": today(),
                },
            ),
            encoding="utf-8",
        )
        artifact = {
                "id": artifact_id,
                "type": args.type,
                "title": args.title,
                "status": status,
                "path": relpath,
                "created_at": today(),
                "updated_at": today(),
                "aliases": [],
                "owners": [],
                "tags": [],
                "supersedes": None,
                "superseded_by": None,
            }
        if args.type == "verification":
            artifact["verification_method"] = method
            artifact["evidence_refs"] = evidence_refs
        registry["artifacts"].append(artifact)
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{artifact_id} {path}")


def cmd_relate(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    if args.relation not in MODEL["relations"]:
        raise KitError(f"unknown relation: {args.relation}")
    with registry_lock(project):
        registry = load_registry(project)
        find_artifact(registry, args.source)
        find_artifact(registry, args.target)
        relation = {"source": args.source, "type": args.relation, "target": args.target}
        if relation not in registry["relations"]:
            registry["relations"].append(relation)
        save_registry(project, registry)
    generate_indexes(project)
    print(json.dumps(relation))


def render_registry_index(registry: dict) -> str:
    rows = [
        "# Artifact Registry",
        "",
        "> Generated from `project.json`; do not edit manually.",
        "",
        "| ID | Type | Status | Title | Path |",
        "|---|---|---|---|---|",
    ]
    for item in sorted(registry["artifacts"], key=lambda x: x["id"]):
        rows.append(
            f"| `{item['id']}` | {item['type']} | {item['status']} | {item['title']} | [{item['path']}](../{item['path']}) |"
        )
    rows += ["", "## Relations", "", "| Source | Relation | Target |", "|---|---|---|"]
    for rel in sorted(
        registry["relations"], key=lambda x: (x["source"], x["type"], x["target"])
    ):
        rows.append(f"| `{rel['source']}` | {rel['type']} | `{rel['target']}` |")
    rows += ["", "## Cycles", "", "| ID | State | Title | Path |", "|---|---|---|---|"]
    for cycle in registry.get("cycles", []):
        rows.append(
            f"| `{cycle['id']}` | {cycle['state']} | {cycle['title']} | "
            f"[{cycle['path']}](../{cycle['path']}) |"
        )
    return "\n".join(rows) + "\n"


def generate_indexes(project: Path) -> None:
    registry = load_registry(project)
    (project / "registry/index.md").write_text(
        render_registry_index(registry), encoding="utf-8"
    )
    (project / "status.md").write_text(render_status(project, registry), encoding="utf-8")
    generate_order_index(project)


def order_dirs(project: Path) -> list[Path]:
    root = project / "registry/agent-orders"
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []


def order_contexts(project: Path) -> list[tuple[Path, dict]]:
    result = []
    for directory in order_dirs(project):
        context = directory / "context.json"
        if context.exists():
            result.append((directory, read_json(context)))
    return result


def render_order_index(project: Path) -> str:
    rows = [
        "# Agent Orders",
        "",
        "> Generated from each order's `context.json`.",
        "",
        "| Order | Title | Domain | Status | Priority | Agent | Updated |",
        "|---|---|---|---|---|---|---|",
    ]
    for directory, ctx in sorted(
        order_contexts(project), key=lambda x: x[1]["order_id"]
    ):
        claim = ctx.get("claim") or {}
        rows.append(
            f"| [{ctx['order_id']}]({directory.name}/order.md) | {ctx['title']} | {ctx['domain']} | {ctx['status']} | {ctx.get('priority', 'normal')} | {claim.get('claimed_by', '')} | {ctx.get('updated_at', '')} |"
        )
    return "\n".join(rows) + "\n"


def generate_order_index(project: Path) -> None:
    root = project / "registry/agent-orders"
    if not root.exists():
        return
    (root / "index.md").write_text(render_order_index(project), encoding="utf-8")


def list_md(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None."


def render_order_text(ctx: dict) -> str:
    completion = ctx.get("completion_marker") or "Not complete."
    values = {
        "order_id": ctx["order_id"],
        "title": ctx["title"],
        "status": ctx["status"],
        "domain": ctx["domain"],
        "priority": ctx.get("priority", "normal"),
        "execution_mode": ctx.get("execution_mode", "handoff"),
        "documentation_mode": ctx.get("documentation_mode", "planned"),
        "objective": ctx["objective"],
        "background": ctx.get("background") or "(TODO: confirm)",
        "authorization": list_md(ctx["authorization"]),
        "scope": list_md(ctx["scope"]),
        "out_of_scope": list_md(ctx["out_of_scope"]),
        "prerequisites": list_md(ctx.get("prerequisites", [])),
        "blast_radius": list_md(ctx.get("blast_radius", [])),
        "execution": list_md(ctx.get("execution", [])),
        "validation": list_md(ctx["validation"]["checks"]),
        "evidence": list_md(ctx.get("evidence", [])),
        "rollback": list_md(ctx["rollback"]["procedure"])
        if ctx["rollback"]["required"]
        else ctx["rollback"].get("justification", "Not required."),
        "expected_result": ctx.get("expected_result") or "(TODO: confirm)",
        "follow_ups": list_md(ctx.get("follow_ups", [])),
        "completion_marker": completion,
    }
    return render_template("order.md.tmpl", values)


def render_order(directory: Path, ctx: dict) -> None:
    (directory / "order.md").write_text(render_order_text(ctx), encoding="utf-8")


def find_order(project: Path, order_id: str) -> tuple[Path, dict]:
    matches = [(d, c) for d, c in order_contexts(project) if c["order_id"] == order_id]
    if len(matches) != 1:
        raise KitError(f"expected one order for {order_id}, found {len(matches)}")
    return matches[0]


def validate_order_context(ctx: dict, path: Path | None = None) -> list[str]:
    errors = []
    required = [
        "schema_version",
        "order_id",
        "title",
        "domain",
        "status",
        "objective",
        "scope",
        "out_of_scope",
        "authorization",
        "constraints",
        "validation",
        "rollback",
    ]
    for key in required:
        if key not in ctx or ctx[key] in ("", [], None):
            errors.append(f"order {ctx.get('order_id', path)} missing {key}")
    if ctx.get("schema_version") != "1.0":
        errors.append(f"order {ctx.get('order_id')} invalid schema_version")
    if not ORDER_ID_RE.fullmatch(ctx.get("order_id", "")):
        errors.append(f"invalid order ID: {ctx.get('order_id')}")
    if ctx.get("status") not in MODEL["order_states"]:
        errors.append(f"order {ctx.get('order_id')} invalid status")
    if contains_secret(ctx):
        errors.append(f"order {ctx.get('order_id')} may contain a secret")
    rollback = ctx.get("rollback") or {}
    if rollback.get("required") and not rollback.get("procedure"):
        errors.append(f"order {ctx.get('order_id')} requires rollback procedure")
    if ctx.get("status") == "closed":
        if not ctx.get("completion_marker"):
            errors.append(f"closed order {ctx.get('order_id')} lacks completion marker")
        if not ctx.get("verification_refs"):
            errors.append(f"closed order {ctx.get('order_id')} lacks verification")
        if not (path and (path.parent / "result.json").exists()):
            errors.append(f"closed order {ctx.get('order_id')} lacks result")
    claim = ctx.get("claim") or {}
    if claim and ctx.get("status") == "claimed":
        try:
            expiry = datetime.fromisoformat(claim["lease_expires_at"])
            if expiry.tzinfo is None:
                raise ValueError("lease timestamp must include timezone")
            if expiry <= datetime.now(timezone.utc).astimezone():
                errors.append(f"order {ctx.get('order_id')} has an expired claim")
        except (KeyError, ValueError):
            errors.append(f"order {ctx.get('order_id')} has invalid claim metadata")
    return errors


def validate_project(project: Path, strict_index: bool = False) -> list[str]:
    errors = []
    registry = load_registry(project)
    if registry.get("schema_version") != "2.1":
        errors.append("registry schema_version must be 2.1")
    mode = registry.get("mode")
    if mode not in MODEL["project_modes"]:
        errors.append(f"invalid project mode: {mode}")
    if registry.get("state") not in MODEL["project_states"]:
        errors.append(f"invalid project state: {registry.get('state')}")
    cycle_ids = [cycle.get("id") for cycle in registry.get("cycles", [])]
    if len(cycle_ids) != len(set(cycle_ids)):
        errors.append("duplicate cycle ID")
    for cycle in registry.get("cycles", []):
        if cycle.get("state") not in MODEL["cycle_states"]:
            errors.append(f"{cycle.get('id')} invalid cycle state: {cycle.get('state')}")
        if not (project / cycle.get("path", "")).is_file():
            errors.append(f"{cycle.get('id')} cycle file missing: {cycle.get('path')}")
        if cycle.get("state") == "completed" and not cycle.get("closure_evidence"):
            errors.append(f"{cycle.get('id')} completed without closure evidence")
        if cycle.get("state") == "completed" and cycle.get("closure_evidence"):
            errors.extend(
                evidence_reference_errors(
                    project,
                    registry,
                    cycle["closure_evidence"],
                    cycle.get("id", "cycle"),
                )
            )
    for active in registry.get("active_cycles", []):
        if active not in cycle_ids:
            errors.append(f"active cycle missing: {active}")
        else:
            cycle = next(value for value in registry["cycles"] if value["id"] == active)
            if cycle.get("state") not in {"active", "blocked"}:
                errors.append(f"active cycle {active} has state {cycle.get('state')}")
    if mode in MODEL["project_modes"] and not MODEL["project_modes"][mode]["parallel"]:
        if len(registry.get("active_cycles", [])) > 1:
            errors.append(f"{mode} mode has more than one active cycle")
    for module in registry.get("modules", []):
        module_spec = MODEL["modules"].get(module)
        if not module_spec:
            errors.append(f"unknown enabled module: {module}")
            continue
        for relpath in module_spec["files"]:
            if not (project / relpath).is_file():
                errors.append(f"module {module} missing file: {relpath}")
    ids = [a.get("id") for a in registry.get("artifacts", [])]
    aliases = [x for a in registry.get("artifacts", []) for x in a.get("aliases", [])]
    for value in set(ids + aliases):
        if (ids + aliases).count(value) > 1:
            errors.append(f"duplicate artifact ID or alias: {value}")
    for artifact in registry.get("artifacts", []):
        spec = MODEL["artifact_types"].get(artifact.get("type"))
        if not spec:
            errors.append(f"{artifact.get('id')} invalid type {artifact.get('type')}")
            continue
        if artifact.get("status") not in spec["states"]:
            errors.append(f"{artifact['id']} invalid status {artifact.get('status')}")
        if not (project / artifact.get("path", "")).is_file():
            errors.append(
                f"{artifact['id']} registered file missing: {artifact.get('path')}"
            )
        if artifact.get("type") == "verification" and artifact.get("status") == "passed":
            if not artifact.get("verification_method"):
                errors.append(f"{artifact['id']} passed without verification method")
            if not artifact.get("evidence_refs"):
                errors.append(f"{artifact['id']} passed without evidence")
            else:
                errors.extend(
                    evidence_reference_errors(
                        project,
                        registry,
                        artifact["evidence_refs"],
                        artifact["id"],
                    )
                )
        if artifact.get("type") == "deliverable" and artifact.get("status") in {
            "verified",
            "accepted",
        }:
            requirement_links = [
                rel
                for rel in registry.get("relations", [])
                if rel.get("source") == artifact.get("id")
                and rel.get("type") in {"addresses", "implements"}
                and any(
                    candidate.get("id") == rel.get("target")
                    and candidate.get("type") == "requirement"
                    for candidate in registry.get("artifacts", [])
                )
            ]
            passed_verifications = [
                rel
                for rel in registry.get("relations", [])
                if rel.get("target") == artifact.get("id")
                and rel.get("type") == "verifies"
                and any(
                    candidate.get("id") == rel.get("source")
                    and candidate.get("type") == "verification"
                    and candidate.get("status") == "passed"
                    for candidate in registry.get("artifacts", [])
                )
            ]
            if not requirement_links:
                errors.append(f"{artifact['id']} lacks a requirement relation")
            if not passed_verifications:
                errors.append(f"{artifact['id']} lacks a passed verification relation")
    known = set(ids) | set(aliases)
    for rel in registry.get("relations", []):
        if rel.get("type") not in MODEL["relations"]:
            errors.append(f"invalid relation type: {rel.get('type')}")
        if rel.get("source") not in known:
            errors.append(f"relation source missing: {rel.get('source')}")
        if rel.get("target") not in known:
            errors.append(f"relation target missing: {rel.get('target')}")
        if rel.get("source") == rel.get("target") and rel.get("type") in {
            "depends_on",
            "supersedes",
            "blocks",
        }:
            errors.append(f"prohibited self relation: {rel}")
    order_ids = []
    for directory, ctx in order_contexts(project):
        order_ids.append(ctx.get("order_id"))
        errors.extend(validate_order_context(ctx, directory / "context.json"))
        rendered = directory / "order.md"
        if not rendered.exists():
            errors.append(f"order {ctx.get('order_id')} missing generated order.md")
        else:
            actual = rendered.read_text(encoding="utf-8")
            expected = render_order_text(ctx)
            if actual != expected:
                errors.append(
                    f"order {ctx.get('order_id')} order.md diverged from context.json"
                )
        result = directory / "result.json"
        if result.exists():
            data = read_json(result)
            errors.extend(
                f"{result}: {error}"
                for error in validate_order_result(data, ctx.get("order_id"))
            )
        for field in (
            "decision_refs",
            "convention_refs",
            "finding_refs",
            "deliverable_refs",
            "verification_refs",
        ):
            for reference in ctx.get(field, []):
                if reference not in known:
                    errors.append(
                        f"order {ctx.get('order_id')} {field} missing: {reference}"
                    )
    for oid in set(order_ids):
        if order_ids.count(oid) > 1:
            errors.append(f"duplicate order ID: {oid}")
    if registry.get("state") == "completed":
        errors.extend(
            f"completed project has {error}"
            for error in project_completion_errors(project, registry)
        )
    if strict_index:
        artifact_actual = (
            (project / "registry/index.md").read_text(encoding="utf-8")
            if (project / "registry/index.md").exists()
            else ""
        )
        order_index = project / "registry/agent-orders/index.md"
        order_actual = (
            order_index.read_text(encoding="utf-8") if order_index.exists() else ""
        )
        status_file = project / "status.md"
        status_actual = (
            status_file.read_text(encoding="utf-8") if status_file.exists() else ""
        )
        if artifact_actual != render_registry_index(registry):
            errors.append("registry index is stale; run `project-kit index`")
        order_root = project / "registry/agent-orders"
        if order_root.exists() and order_actual != render_order_index(project):
            errors.append("agent-order index is stale; run `project-kit index`")
        if status_actual != render_status(project, registry):
            errors.append("status view is stale; run `project-kit index`")
    return errors


def cmd_validate(args: argparse.Namespace) -> None:
    errors = validate_project(project_arg(args.project), args.strict_index)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        raise KitError(f"validation failed with {len(errors)} error(s)")
    print("PASS")


def cmd_index(args: argparse.Namespace) -> None:
    generate_indexes(project_arg(args.project))
    print("indexes regenerated")


def cmd_audit(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    errors = validate_project(project, strict_index=True)
    lines = [
        f"# Registry Audit — {today()}",
        "",
        f"**Verdict:** {'PASS' if not errors else 'NEEDS FIXES'}",
        "",
        "## Findings",
        "",
    ]
    lines.extend(
        [f"- {error}" for error in errors]
        or ["- No registry integrity defects detected."]
    )
    text = "\n".join(lines) + "\n"
    if args.write_report:
        report = project / "registry/audit-report.md"
        report.write_text(text, encoding="utf-8")
        print(report)
    else:
        print(text, end="")
    if errors:
        raise KitError(f"audit found {len(errors)} issue(s)")


def cmd_show(args: argparse.Namespace) -> None:
    registry = load_registry(project_arg(args.project))
    print(json.dumps(find_artifact(registry, args.id), indent=2))


def cmd_supersede(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        old = find_artifact(registry, args.id)
        new = find_artifact(registry, args.by)
        old["status"] = "superseded"
        old["superseded_by"] = new["id"]
        new["supersedes"] = old["id"]
        old["updated_at"] = new["updated_at"] = today()
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{old['id']} superseded by {new['id']}")


def cmd_archive(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        artifact = find_artifact(registry, args.id)
        if "archived" not in MODEL["artifact_types"][artifact["type"]]["states"]:
            raise KitError(f"{artifact['type']} cannot be archived")
        artifact["status"] = "archived"
        artifact["updated_at"] = today()
        save_registry(project, registry)
    generate_indexes(project)
    print(f"{artifact['id']} archived")


def cmd_convention_list(args: argparse.Namespace) -> None:
    registry = load_registry(project_arg(args.project))
    values = [
        a
        for a in registry["artifacts"]
        if a["type"] == "convention" and (not args.status or a["status"] == args.status)
    ]
    for item in values:
        print(f"{item['id']}\t{item['status']}\t{item['title']}")


def order_create(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    with registry_lock(project):
        registry = load_registry(project)
        prefix = args.domain.upper().replace("-", "")
        order_id = args.id or next_id(registry, "decision", prefix=prefix, width=4)
        if not ORDER_ID_RE.fullmatch(order_id):
            raise KitError(f"invalid order ID: {order_id}")
        if any(c["order_id"] == order_id for _, c in order_contexts(project)):
            raise KitError(f"duplicate order ID: {order_id}")
        directory = (
            project / "registry/agent-orders" / f"{order_id.lower()}-{slug(args.title)}"
        )
        directory.mkdir(parents=True)
        ctx = {
            "schema_version": "1.0",
            "order_id": order_id,
            "title": args.title,
            "domain": args.domain,
            "status": "draft",
            "priority": args.priority,
            "created_at": now(),
            "updated_at": now(),
            "execution_mode": args.execution_mode,
            "documentation_mode": args.documentation_mode,
            "objective": args.objective or args.title,
            "background": "",
            "authorization": ["Read and modify only the declared scope."],
            "scope": args.scope or ["(TODO: confirm)"],
            "out_of_scope": args.out_of_scope or ["Unrelated systems and files."],
            "prerequisites": [],
            "blast_radius": [],
            "execution": [],
            "constraints": {},
            "validation": {
                "required": True,
                "checks": ["Verify the observable final state."],
            },
            "evidence": [],
            "rollback": {
                "required": True,
                "procedure": [
                    "Restore the pre-change state from the recorded backup or diff."
                ],
            },
            "expected_result": args.objective or args.title,
            "follow_ups": [],
            "decision_refs": args.decision or [],
            "convention_refs": [],
            "finding_refs": [],
            "deliverable_refs": [],
            "verification_refs": [],
            "required_credentials": [],
            "claim": None,
            "completion_marker": None,
        }
        write_json(directory / "context.json", ctx)
        render_order(directory, ctx)
        (directory / "execution-log.md").write_text(
            f"# {order_id} Execution Log\n\n- {now()} — Order created in DRAFT.\n",
            encoding="utf-8",
        )
        save_registry(project, registry)
    generate_order_index(project)
    print(order_id)


def update_order(project: Path, order_id: str, mutator) -> dict:
    with registry_lock(project):
        directory, ctx = find_order(project, order_id)
        mutator(directory, ctx)
        ctx["updated_at"] = now()
        errors = validate_order_context(ctx, directory / "context.json")
        if errors:
            raise KitError("; ".join(errors))
        write_json(directory / "context.json", ctx)
        render_order(directory, ctx)
    generate_order_index(project)
    return ctx


def transition(ctx: dict, target: str, retrospective: bool = False) -> None:
    current = ctx["status"]
    if (
        retrospective
        and ctx.get("documentation_mode") == "retrospective"
        and target in {"executed", "verified", "closed"}
    ):
        ctx["status"] = target
        return
    if target not in MODEL["order_transitions"].get(current, []):
        raise KitError(f"invalid order transition: {current} -> {target}")
    ctx["status"] = target


def order_show(args: argparse.Namespace) -> None:
    _, ctx = find_order(project_arg(args.project), args.id)
    print(json.dumps(ctx, indent=2))


def order_state(args: argparse.Namespace) -> None:
    project = project_arg(args.project)

    def mutate(directory, ctx):
        transition(ctx, args.target, args.retrospective)
        if args.target == "blocked" and not args.reason:
            raise KitError("blocking requires --reason")
        with (directory / "execution-log.md").open("a", encoding="utf-8") as handle:
            handle.write(
                f"- {now()} — Status: {args.target}"
                + (f" — {args.reason}" if args.reason else "")
                + "\n"
            )

    print(update_order(project, args.id, mutate)["status"])


def order_claim(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    if args.hours <= 0:
        raise KitError("claim hours must be greater than zero")

    def mutate(directory, ctx):
        existing = ctx.get("claim")
        if existing:
            try:
                expiry = datetime.fromisoformat(existing["lease_expires_at"])
                if expiry.tzinfo is None:
                    raise ValueError("lease timestamp must include timezone")
            except (KeyError, ValueError) as exc:
                raise KitError("existing claim has invalid lease metadata") from exc
            if expiry > datetime.now(timezone.utc).astimezone():
                raise KitError(f"order already claimed by {existing['claimed_by']}")
            if not args.recover_expired:
                raise KitError(
                    "order has an expired claim; pass --recover-expired to recover it"
                )
        if ctx["status"] == "ready":
            transition(ctx, "claimed")
        elif ctx["status"] != "claimed":
            raise KitError("only READY or expired CLAIMED orders can be claimed")
        start = datetime.now(timezone.utc).astimezone()
        ctx["claim"] = {
            "status": "claimed",
            "claimed_by": args.agent,
            "claimed_at": start.isoformat(timespec="seconds"),
            "lease_expires_at": (start + timedelta(hours=args.hours)).isoformat(
                timespec="seconds"
            ),
            "working_tree": args.working_tree or str(project),
        }
        with (directory / "execution-log.md").open("a", encoding="utf-8") as handle:
            handle.write(f"- {now()} — Claimed by {args.agent}.\n")

    print(update_order(project, args.id, mutate)["claim"]["claimed_by"])


def order_release(args: argparse.Namespace) -> None:
    project = project_arg(args.project)

    def mutate(directory, ctx):
        if not ctx.get("claim"):
            raise KitError("order has no active claim")
        if args.agent and ctx["claim"].get("claimed_by") != args.agent:
            raise KitError("claim owner mismatch")
        ctx["claim"] = None
        if ctx["status"] == "claimed":
            ctx["status"] = "ready"
        with (directory / "execution-log.md").open("a", encoding="utf-8") as handle:
            handle.write(f"- {now()} — Claim released.\n")

    update_order(project, args.id, mutate)
    print("released")


def order_transfer(args: argparse.Namespace) -> None:
    project = project_arg(args.project)

    def mutate(directory, ctx):
        if not ctx.get("claim"):
            raise KitError("order has no active claim")
        previous = ctx["claim"]["claimed_by"]
        ctx["claim"]["claimed_by"] = args.to_agent
        ctx["claim"]["claimed_at"] = now()
        with (directory / "execution-log.md").open("a", encoding="utf-8") as handle:
            handle.write(
                f"- {now()} — Claim transferred from {previous} to {args.to_agent}.\n"
            )

    update_order(project, args.id, mutate)
    print(args.to_agent)


def order_handoff(args: argparse.Namespace) -> None:
    directory, ctx = find_order(project_arg(args.project), args.id)
    payload = {
        k: ctx.get(k)
        for k in [
            "schema_version",
            "order_id",
            "title",
            "domain",
            "status",
            "priority",
            "objective",
            "background",
            "authorization",
            "scope",
            "out_of_scope",
            "prerequisites",
            "blast_radius",
            "execution",
            "constraints",
            "validation",
            "evidence",
            "rollback",
            "expected_result",
            "follow_ups",
            "decision_refs",
            "convention_refs",
            "finding_refs",
            "deliverable_refs",
            "verification_refs",
            "required_credentials",
            "claim",
        ]
    }
    if args.format == "json":
        text = json.dumps(payload, indent=2) + "\n"
    else:
        text = f"# Handoff: {ctx['order_id']} — {ctx['title']}\n\n## Objective\n\n{ctx['objective']}\n\n## Scope\n\n{list_md(ctx['scope'])}\n\n## Out of scope\n\n{list_md(ctx['out_of_scope'])}\n\n## Execution\n\n{list_md(ctx.get('execution', []))}\n\n## Validation\n\n{list_md(ctx['validation']['checks'])}\n\n## Rollback\n\n{list_md(ctx['rollback']['procedure'])}\n"
    if contains_secret(text):
        raise KitError("handoff may contain a secret")
    output = directory / f"handoff.{'json' if args.format == 'json' else 'md'}"
    output.write_text(text, encoding="utf-8")
    print(output)


def order_record_result(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    source = Path(args.result).resolve()
    result = read_json(source)

    def mutate(directory, ctx):
        result_errors = validate_order_result(result, ctx["order_id"])
        if result_errors:
            raise KitError("invalid order result: " + "; ".join(result_errors))
        if result["status"] == "failed":
            if "failed" not in MODEL["order_transitions"].get(ctx["status"], []):
                raise KitError("failed result requires an active order")
            transition(ctx, "failed")
        elif ctx["status"] == "in_progress":
            transition(ctx, "executed")
        elif (
            ctx["status"] == "draft"
            and ctx.get("documentation_mode") == "retrospective"
        ):
            transition(ctx, "executed", retrospective=True)
        else:
            raise KitError(
                "successful result requires an IN_PROGRESS order or retrospective draft"
            )
        write_json(directory / "result.json", result)
        with (directory / "execution-log.md").open("a", encoding="utf-8") as handle:
            handle.write(
                f"- {now()} — Structured result recorded from {source.name}.\n"
            )

    update_order(project, args.id, mutate)
    print("result recorded")


def order_verify(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    registry = load_registry(project)
    verification = find_artifact(registry, args.verification)
    if verification.get("type") != "verification":
        raise KitError(f"{args.verification} is not a verification artifact")
    if verification.get("status") != "passed":
        raise KitError(f"{args.verification} is not passed")
    verification_errors = []
    if not verification.get("verification_method"):
        verification_errors.append("verification method is missing")
    if not verification.get("evidence_refs"):
        verification_errors.append("verification evidence is missing")
    else:
        verification_errors.extend(
            evidence_reference_errors(
                project,
                registry,
                verification["evidence_refs"],
                verification["id"],
            )
        )
    if verification_errors:
        raise KitError(
            f"{verification['id']} is not valid evidence: "
            + "; ".join(verification_errors)
        )

    def mutate(directory, ctx):
        result_path = directory / "result.json"
        if not result_path.exists():
            raise KitError("cannot verify without result.json")
        result = read_json(result_path)
        result_errors = validate_order_result(result, ctx["order_id"])
        if result_errors:
            raise KitError("cannot verify invalid result.json: " + "; ".join(result_errors))
        if result["status"] == "failed" or result["validation"]["status"] == "failed":
            raise KitError("cannot verify a failed execution result")
        if ctx["status"] == "executed":
            transition(ctx, "verified")
        elif ctx["status"] != "verified":
            raise KitError("order must be EXECUTED to verify")
        if args.verification not in ctx["verification_refs"]:
            ctx["verification_refs"].append(args.verification)
        with (directory / "execution-log.md").open("a", encoding="utf-8") as handle:
            handle.write(f"- {now()} — Verified by {args.verification}.\n")

    update_order(project, args.id, mutate)
    print("verified")


def order_close(args: argparse.Namespace) -> None:
    project = project_arg(args.project)

    def mutate(directory, ctx):
        if ctx["status"] != "verified":
            raise KitError("only VERIFIED orders can close")
        if not ctx["verification_refs"] or not (directory / "result.json").exists():
            raise KitError("close requires verification and result.json")
        result_errors = validate_order_result(
            read_json(directory / "result.json"), ctx["order_id"]
        )
        if result_errors:
            raise KitError("close requires valid result.json: " + "; ".join(result_errors))
        transition(ctx, "closed")
        ctx["claim"] = None
        ctx["completion_marker"] = f"{ctx['order_id']}: CLOSED {today()}"
        with (directory / "execution-log.md").open("a", encoding="utf-8") as handle:
            handle.write(f"- {now()} — Closed.\n")

    update_order(project, args.id, mutate)
    print("closed")


def order_import(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        raise KitError(f"missing source order: {source}")
    historical = source.read_text(encoding="utf-8")
    title_line = next(
        (
            line.lstrip("# ").strip()
            for line in historical.splitlines()
            if line.startswith("#")
        ),
        source.stem,
    )
    synthetic = argparse.Namespace(
        project=str(project),
        domain=args.domain,
        title=title_line,
        objective=f"Retrospective record imported from {source.name}.",
        id=args.id,
        priority="normal",
        execution_mode="direct",
        documentation_mode=args.mode,
        decision=[],
        scope=[f"Historical actions documented in {source.name}."],
        out_of_scope=["Re-executing any historical action."],
    )
    order_create(synthetic)

    def section(start: str, end: str | None) -> str:
        if start not in historical:
            return ""
        value = historical.split(start, 1)[1]
        if end and end in value:
            value = value.split(end, 1)[0]
        return value.strip()

    def enrich(directory, ctx):
        ctx["background"] = section("## 0. Background", "## 1.")
        blast = section("## 1. Blast-radius investigation", "## 2.")
        execution = section("## 2. What was done", "## 3.")
        rollback = section("## 3. Rollback", "## 4.")
        follow = section("## 4. Follow-ups", "## Execution log")
        ctx["blast_radius"] = [blast] if blast else []
        ctx["execution"] = [execution] if execution else []
        ctx["rollback"] = {
            "required": True,
            "procedure": [
                rollback or "Use the historical source document rollback section."
            ],
        }
        ctx["follow_ups"] = [
            line[2:].strip() for line in follow.splitlines() if line.startswith("- ")
        ]
        ctx["decision_refs"] = sorted(set(re.findall(r"\bD-[0-9]{3}\b", historical)))
        ctx["expected_result"] = (
            "Preserve the historical final state without re-executing the order."
        )

    update_order(project, args.id, enrich)
    directory, _ = find_order(project, args.id)
    shutil.copy2(source, directory / "historical-source.md")
    print(directory)


def cmd_migrate(args: argparse.Namespace) -> None:
    project = project_arg(args.project)
    legacy = [
        p.name
        for p in project.glob("*.md")
        if p.name not in {"index.md", "requirements.md", "plan.md", "audit.md"}
    ]
    report = {
        "project": str(project),
        "mode": "apply" if args.apply else "dry-run",
        "legacy_root_documents": sorted(legacy),
        "actions": [
            "create registry/project.json if absent",
            "preserve existing IDs and files",
            "register metadata only after explicit review",
        ],
        "automatic_changes": [],
    }
    if args.apply and not KEBAB_RE.fullmatch(project.name):
        raise KitError("legacy project directory name must be descriptive kebab-case")
    if args.apply and not registry_path(project).exists():
        backup = (
            project
            / f"registry/migration-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        )
        backup.parent.mkdir(parents=True, exist_ok=True)
        write_json(backup, report)
        requested_modules = ["core", "decisions", "risks", "tasks"]
        registry = {
            "schema_version": "2.1",
            "project": project.name,
            "profile": "minimal",
            "mode": "flexible",
            "state": "planned",
            "created_at": now(),
            "updated_at": now(),
            "modules": [],
            "counters": {},
            "artifacts": [],
            "relations": [],
            "cycles": [],
            "active_cycles": [],
            "status_history": [
                {
                    "at": now(),
                    "state": "planned",
                    "summary": "Legacy project registry created by migration.",
                }
            ],
        }
        for module in requested_modules:
            add_module(project, module, registry)
        create_cycle(project, registry, "Migration workstream")
        save_registry(project, registry)
        report["automatic_changes"].append(str(registry_path(project)))
    if args.apply:
        generate_indexes(project)
        migration_errors = validate_project(project, strict_index=True)
        if migration_errors:
            raise KitError(
                "migration produced an invalid project: "
                + "; ".join(migration_errors)
            )
    output = (
        project / "registry/migration-report.json"
        if args.apply
        else Path.cwd() / f"{project.name}-migration-dry-run.json"
    )
    write_json(output, report)
    print(output)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="project-kit")
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("init")
    x.add_argument("name")
    x.add_argument("--root", default="agentic-workspace/projects")
    x.add_argument("--mode", choices=MODEL["project_modes"], default="flexible")
    x.add_argument("--profile", choices=MODEL["profiles"], default="standard")
    x.add_argument(
        "--with", dest="with_modules", action="append", choices=MODEL["modules"]
    )
    x.set_defaults(func=cmd_init)
    x = sub.add_parser("add-module")
    x.add_argument("project")
    x.add_argument("module", choices=MODEL["modules"])
    x.set_defaults(func=cmd_add_module)
    x = sub.add_parser("create")
    x.add_argument("project")
    x.add_argument("type", choices=MODEL["artifact_types"])
    x.add_argument("--title", required=True)
    x.add_argument("--status")
    x.add_argument("--id")
    x.add_argument("--method")
    x.add_argument("--evidence", action="append")
    x.set_defaults(func=cmd_create)
    x = sub.add_parser("relate")
    x.add_argument("project")
    x.add_argument("source")
    x.add_argument("relation", choices=MODEL["relations"])
    x.add_argument("target")
    x.set_defaults(func=cmd_relate)
    x = sub.add_parser("validate")
    x.add_argument("project")
    x.add_argument("--strict-index", action="store_true")
    x.set_defaults(func=cmd_validate)
    x = sub.add_parser("index")
    x.add_argument("project")
    x.set_defaults(func=cmd_index)
    x = sub.add_parser("audit")
    x.add_argument("project")
    x.add_argument("--write-report", action="store_true")
    x.set_defaults(func=cmd_audit)
    x = sub.add_parser("show")
    x.add_argument("project")
    x.add_argument("id")
    x.set_defaults(func=cmd_show)
    x = sub.add_parser("supersede")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--by", required=True)
    x.set_defaults(func=cmd_supersede)
    x = sub.add_parser("archive")
    x.add_argument("project")
    x.add_argument("id")
    x.set_defaults(func=cmd_archive)
    cycle = sub.add_parser("cycle").add_subparsers(
        dest="cycle_command", required=True
    )
    x = cycle.add_parser("create")
    x.add_argument("project")
    x.add_argument("--title", required=True)
    x.set_defaults(func=cmd_cycle_create)
    x = cycle.add_parser("list")
    x.add_argument("project")
    x.set_defaults(func=cmd_cycle_list)
    x = cycle.add_parser("start")
    x.add_argument("project")
    x.add_argument("id")
    x.set_defaults(func=cmd_cycle_start)
    x = cycle.add_parser("close")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--evidence", action="append", required=True)
    x.set_defaults(func=cmd_cycle_close)
    status = sub.add_parser("status").add_subparsers(
        dest="status_command", required=True
    )
    x = status.add_parser("update")
    x.add_argument("project")
    x.add_argument("--state", choices=MODEL["project_states"], required=True)
    x.add_argument("--summary", required=True)
    x.set_defaults(func=cmd_status_update)
    x = status.add_parser("show")
    x.add_argument("project")
    x.set_defaults(func=cmd_status_show)
    artifact = sub.add_parser("artifact").add_subparsers(
        dest="artifact_command", required=True
    )
    x = artifact.add_parser("set-status")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("state")
    x.add_argument("--method")
    x.add_argument("--evidence", action="append")
    x.set_defaults(func=cmd_artifact_status)
    x = sub.add_parser("migrate")
    x.add_argument("project")
    mode = x.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    x.set_defaults(func=cmd_migrate)
    decision = sub.add_parser("decision").add_subparsers(
        dest="decision_command", required=True
    )
    x = decision.add_parser("create")
    x.add_argument("project")
    x.add_argument("--title", required=True)
    x.add_argument("--status", default="draft")
    x.add_argument("--id")
    x.set_defaults(func=cmd_create, type="decision")
    x = decision.add_parser("show")
    x.add_argument("project")
    x.add_argument("id")
    x.set_defaults(func=cmd_show)
    x = decision.add_parser("supersede")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--by", required=True)
    x.set_defaults(func=cmd_supersede)
    convention = sub.add_parser("convention").add_subparsers(
        dest="convention_command", required=True
    )
    x = convention.add_parser("create")
    x.add_argument("project")
    x.add_argument("--title", required=True)
    x.add_argument("--status", default="draft")
    x.add_argument("--id")
    x.set_defaults(func=cmd_create, type="convention")
    x = convention.add_parser("list")
    x.add_argument("project")
    x.add_argument("--status")
    x.set_defaults(func=cmd_convention_list)
    order = sub.add_parser("order").add_subparsers(dest="order_command", required=True)
    x = order.add_parser("create")
    x.add_argument("project")
    x.add_argument("--domain", required=True)
    x.add_argument("--title", required=True)
    x.add_argument("--objective")
    x.add_argument("--id")
    x.add_argument("--priority", default="normal")
    x.add_argument(
        "--execution-mode",
        choices=["handoff", "direct", "automated", "manual", "orchestrated"],
        default="handoff",
    )
    x.add_argument(
        "--documentation-mode", choices=["planned", "retrospective"], default="planned"
    )
    x.add_argument("--decision", action="append")
    x.add_argument("--scope", action="append")
    x.add_argument("--out-of-scope", action="append")
    x.set_defaults(func=order_create)
    for name in ["show", "status"]:
        x = order.add_parser(name)
        x.add_argument("project")
        x.add_argument("id")
        x.set_defaults(func=order_show)
    x = order.add_parser("claim")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--agent", required=True)
    x.add_argument("--hours", type=int, default=4)
    x.add_argument("--working-tree")
    x.add_argument("--recover-expired", action="store_true")
    x.set_defaults(func=order_claim)
    x = order.add_parser("release")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--agent")
    x.set_defaults(func=order_release)
    x = order.add_parser("transfer")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--to-agent", required=True)
    x.set_defaults(func=order_transfer)
    for name, target in [
        ("ready", "ready"),
        ("start", "in_progress"),
        ("block", "blocked"),
        ("resume", "in_progress"),
        ("cancel", "cancelled"),
    ]:
        x = order.add_parser(name)
        x.add_argument("project")
        x.add_argument("id")
        x.add_argument("--reason")
        x.add_argument("--retrospective", action="store_true")
        x.set_defaults(func=order_state, target=target)
    x = order.add_parser("handoff")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--format", choices=["markdown", "json"], default="markdown")
    x.set_defaults(func=order_handoff)
    x = order.add_parser("record-result")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--result", required=True)
    x.set_defaults(func=order_record_result)
    x = order.add_parser("verify")
    x.add_argument("project")
    x.add_argument("id")
    x.add_argument("--verification", required=True)
    x.set_defaults(func=order_verify)
    x = order.add_parser("close")
    x.add_argument("project")
    x.add_argument("id")
    x.set_defaults(func=order_close)
    x = order.add_parser("import")
    x.add_argument("project")
    x.add_argument("source")
    x.add_argument("--id", required=True)
    x.add_argument("--domain", required=True)
    x.add_argument("--mode", choices=["retrospective"], default="retrospective")
    x.set_defaults(func=order_import)
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        args.func(args)
        return 0
    except KitError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
