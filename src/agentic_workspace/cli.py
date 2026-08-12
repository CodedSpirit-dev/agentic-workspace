from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from pathlib import PureWindowsPath

from . import __version__


PRODUCT_ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_ROOT = Path(__file__).resolve().parent / "payload"
MANIFEST = Path("agentic-workspace/.managed-manifest.json")
MANAGED_MARKER = "<!-- managed-by: agentic-workspace -->"


class InstallError(RuntimeError):
    pass


@dataclass
class Report:
    target: Path
    dry_run: bool = False
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    linked: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def changed(self, path: Path, update: bool = False) -> None:
        rel = display_path(path, self.target)
        (self.updated if update else self.created).append(rel)

    def print(self) -> None:
        prefix = "Dry run" if self.dry_run else "Installed"
        print(f"{prefix} agentic-workspace {__version__} in {self.target}")
        for label, values in (
            ("created", self.created),
            ("updated", self.updated),
            ("linked", self.linked),
            ("preserved", self.preserved),
        ):
            if values:
                print(f"  {label}: {len(values)}")
        for warning in self.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def digest_path(path: Path) -> str:
    if path.is_symlink():
        raise InstallError(f"cannot hash symlink as managed content: {path}")
    if path.is_file():
        return digest_bytes(b"file\0" + path.read_bytes())
    if not path.is_dir():
        raise InstallError(f"cannot hash missing managed content: {path}")
    digest = hashlib.sha256(b"directory\0")
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise InstallError(f"managed copy contains a symlink: {item}")
        if item.is_file():
            digest.update(str(item.relative_to(path)).encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def require_contained(path: Path, target: Path, *, parent: bool = False) -> Path:
    """Reject paths whose existing symlink components escape the install target."""
    candidate = path.parent if parent else path
    root = target.resolve()
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise InstallError(f"path escapes target directory: {path}") from exc
    return path


def managed_path(target: Path, rel: str) -> Path:
    if not isinstance(rel, str):
        raise InstallError(f"managed path must be a string: {rel!r}")
    value = Path(rel)
    windows_value = PureWindowsPath(rel)
    if value.is_absolute() or windows_value.is_absolute() or windows_value.drive:
        raise InstallError(f"managed path must be repository-relative: {rel}")
    return require_contained(target / value, target, parent=True)


def load_manifest(target: Path) -> dict:
    path = require_contained(target / MANIFEST, target, parent=True)
    if path.is_symlink():
        raise InstallError(f"managed manifest must not be a symlink: {path}")
    if not path.exists():
        return {"files": {}, "links": {}, "entry_points": {}, "generated_files": {}, "adapter_hashes": {}}
    if not path.is_file():
        raise InstallError(f"managed manifest is not a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"invalid managed manifest: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InstallError(f"invalid managed manifest root: expected object: {path}")
    for key in ("files", "links", "entry_points", "generated_files", "adapter_hashes"):
        current = value.setdefault(key, {})
        if not isinstance(current, dict) or not all(
            isinstance(item, str) and isinstance(expected, str)
            for item, expected in current.items()
        ):
            raise InstallError(f"invalid managed manifest field {key}: expected string map: {path}")
    if "git_hook_required" in value and not isinstance(value["git_hook_required"], bool):
        raise InstallError(f"invalid managed manifest field git_hook_required: expected boolean: {path}")
    return value


def write_text(path: Path, text: str, report: Report, *, overwrite: bool = True) -> bool:
    require_contained(path, report.target, parent=True)
    encoded = text.encode("utf-8")
    existed = path.exists() or path.is_symlink()
    if existed and not path.is_symlink() and path.is_file() and path.read_bytes() == encoded:
        return True
    if existed and not overwrite:
        report.preserved.append(display_path(path, report.target))
        return False
    if existed and not path.is_symlink() and not path.is_file():
        rel = display_path(path, report.target)
        report.preserved.append(rel)
        report.warnings.append(f"non-file destination was preserved: {rel}")
        return False
    if report.dry_run:
        report.changed(path, update=existed)
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        path.unlink()
    path.write_bytes(encoded)
    report.changed(path, update=existed)
    return True


def copy_payload(target: Path, previous: dict, report: Report) -> dict[str, str]:
    if not PAYLOAD_ROOT.is_dir():
        raise InstallError(f"payload not found: {PAYLOAD_ROOT}")
    hashes: dict[str, str] = {}
    previous_hashes = previous.get("files", {})
    for source in sorted(
        path
        for path in PAYLOAD_ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    ):
        rel = source.relative_to(PAYLOAD_ROOT)
        destination = require_contained(target / rel, target, parent=True)
        new_hash = digest_file(source)
        hashes[str(rel)] = new_hash
        existed = destination.exists() or destination.is_symlink()
        safe = not existed
        if existed and destination.is_file() and not destination.is_symlink():
            current_hash = digest_file(destination)
            safe = current_hash == new_hash or current_hash == previous_hashes.get(str(rel))
        if not safe:
            report.preserved.append(str(rel))
            report.warnings.append(f"kept locally modified managed file: {rel}")
            hashes[str(rel)] = previous_hashes.get(str(rel), new_hash)
            continue
        if existed and destination.is_file() and digest_file(destination) == new_hash:
            continue
        if report.dry_run:
            report.changed(destination, update=existed)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            destination.unlink()
        shutil.copy2(source, destination)
        report.changed(destination, update=existed)
    return hashes


def unique_backup(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def instruction_source(path: Path) -> str | None:
    if not path.exists() or path.is_symlink() or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if MANAGED_MARKER in text:
        return None
    return text


def migrate_instructions(target: Path, previous: dict, report: Report) -> dict[str, str]:
    agents = target / "AGENTS.md"
    claude = target / "CLAUDE.md"
    sources: list[tuple[str, str]] = []
    for label, path in (("agents", agents), ("claude", claude)):
        content = instruction_source(path)
        if content is not None and all(content != prior for _, prior in sources):
            sources.append((label, content))

    imported_links: list[str] = []
    for label, content in sources:
        backup = unique_backup(target / f"agentic-workspace/docs/imported/{label}-original.md")
        write_text(backup, content, report, overwrite=False)
        imported_links.append(f"- [`{backup.name}`](imported/{backup.name})")

    guide = target / "agentic-workspace/docs/repository-guide.md"
    if sources and not guide.exists():
        body = (
            "# Repository guide\n\n"
            "The installer preserved the repository instructions that existed before "
            "agentic-workspace was adopted. Consolidate durable repository-specific "
            "architecture, commands, safety rules, and conventions here. Keep the source "
            "copies below unchanged as migration evidence.\n\n"
            "## Imported sources\n\n"
            + "\n".join(imported_links)
            + "\n"
        )
        write_text(guide, body, report, overwrite=False)
    elif not guide.exists():
        write_text(
            guide,
            "# Repository guide\n\n"
            "Document repository-specific architecture, setup, commands, conventions, "
            "and safety constraints here. Keep claims source-backed and move work-specific "
            "state into its project, plan, task, or session note.\n\n"
            "## Architecture\n\n(TODO: confirm)\n\n"
            "## Development commands\n\n(TODO: confirm)\n\n"
            "## Conventions and risks\n\n(TODO: confirm)\n",
            report,
            overwrite=False,
        )

    root_agents = f"""{MANAGED_MARKER}
# Agent entry point

Before working in this repository, read [`agentic-workspace/docs/index.md`](agentic-workspace/docs/index.md).

Use the indexed documentation, project registry, skills, agents, and hooks from
`agentic-workspace/`. Keep detailed repository knowledge out of this file so Codex,
Claude Code, Hermes, and other agents share the same source of truth.
"""
    root_agents_hash = digest_bytes(root_agents.encode("utf-8"))
    previous_hash = previous.get("entry_points", {}).get("AGENTS.md")
    current_managed_hash: str | None = None
    if agents.exists() and not agents.is_symlink() and agents.is_file():
        current = agents.read_text(encoding="utf-8")
        if MANAGED_MARKER in current:
            current_managed_hash = digest_bytes(current.encode("utf-8"))

    if (
        current_managed_hash is not None
        and current_managed_hash != root_agents_hash
        and current_managed_hash != previous_hash
    ):
        report.preserved.append("AGENTS.md")
        report.warnings.append("kept locally modified managed entry point: AGENTS.md")
    else:
        write_text(agents, root_agents, report)
    entry_point_hash = (
        previous_hash
        if previous_hash and current_managed_hash not in {None, previous_hash, root_agents_hash}
        else root_agents_hash
    )

    if report.dry_run:
        report.linked.append("CLAUDE.md -> AGENTS.md")
        return {"AGENTS.md": entry_point_hash}
    if claude.is_symlink() and os.readlink(claude) == "AGENTS.md":
        return {"AGENTS.md": entry_point_hash}
    if claude.exists() or claude.is_symlink():
        claude.unlink()
    try:
        claude.symlink_to("AGENTS.md")
        report.linked.append("CLAUDE.md -> AGENTS.md")
    except OSError:
        write_text(claude, agents.read_text(encoding="utf-8"), report)
        report.warnings.append("symlinks unavailable; CLAUDE.md is a managed copy")
    return {"AGENTS.md": entry_point_hash}


def ensure_link(
    link: Path,
    target: str,
    report: Report,
    *,
    source: Path | None = None,
    previous_hash: str | None = None,
) -> bool:
    require_contained(link, report.target, parent=True)
    source = source or (link.parent / target).resolve(strict=False)
    if not report.dry_run or source.is_relative_to(report.target):
        require_contained(source, report.target)
    elif not source.is_relative_to(PAYLOAD_ROOT):
        raise InstallError(f"adapter source is outside the packaged payload: {source}")
    if not source.exists():
        raise InstallError(f"adapter source does not exist: {source}")
    if link.is_symlink() and os.readlink(link) == target and link.resolve(strict=False) == source:
        return True
    if link.exists() and not link.is_symlink() and same_content(link, source):
        return True
    if link.exists() or link.is_symlink():
        managed_copy = False
        if previous_hash and not link.is_symlink():
            try:
                managed_copy = digest_path(link) == previous_hash
            except InstallError:
                managed_copy = False
        if not managed_copy:
            report.preserved.append(display_path(link, report.target))
            report.warnings.append(f"adapter already exists and was preserved: {display_path(link, report.target)}")
            return False
        if report.dry_run:
            report.changed(link, update=True)
            return True
        if link.is_dir():
            shutil.rmtree(link)
        else:
            link.unlink()
    if report.dry_run:
        report.linked.append(f"{display_path(link, report.target)} -> {target}")
        return True
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target, target_is_directory=source.is_dir())
    except (NotImplementedError, OSError):
        if source.is_dir():
            shutil.copytree(source, link)
        else:
            shutil.copy2(source, link)
        report.warnings.append(f"symlinks unavailable; copied adapter: {display_path(link, report.target)}")
    report.linked.append(f"{display_path(link, report.target)} -> {target}")
    return True


def same_content(left: Path, right: Path) -> bool:
    if left.is_symlink() or right.is_symlink():
        return False
    if left.is_file() and right.is_file():
        return digest_file(left) == digest_file(right)
    if not left.is_dir() or not right.is_dir():
        return False
    try:
        return digest_path(left) == digest_path(right)
    except InstallError:
        return False


def write_generated_text(
    path: Path,
    text: str,
    previous_hash: str | None,
    report: Report,
) -> str | None:
    encoded = text.encode("utf-8")
    expected_hash = digest_bytes(encoded)
    existed = path.exists() or path.is_symlink()
    current_hash = None
    if existed and not path.is_symlink() and path.is_file():
        current_hash = digest_file(path)
        if current_hash == expected_hash:
            return expected_hash
    if existed and (
        current_hash is None or previous_hash is None or current_hash != previous_hash
    ):
        rel = display_path(path, report.target)
        report.preserved.append(rel)
        report.warnings.append(f"generated adapter conflict preserved: {rel}")
        return previous_hash
    if not write_text(path, text, report):
        return previous_hash
    return expected_hash


def parse_agent(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    name = path.stem.replace("-", "_")
    description = f"Specialized {path.stem.replace('-', ' ')} agent."
    body = text
    if text.startswith("---\n"):
        _, front, body = text.split("---\n", 2)
        for line in front.splitlines():
            key, _, value = line.partition(":")
            if key.strip() == "name":
                name = value.strip().replace("-", "_")
            elif key.strip() == "description":
                description = value.strip()
    return name, description, body.strip()


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def install_adapters(
    target: Path, previous: dict, report: Report
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    links: dict[str, str] = {}
    adapter_hashes: dict[str, str] = {}
    generated_files: dict[str, str] = {}
    previous_adapter_hashes = previous.get("adapter_hashes", {})
    previous_generated = previous.get("generated_files", {})
    skills = target / "agentic-workspace/skills"
    if not skills.exists():
        skills = PAYLOAD_ROOT / "agentic-workspace/skills"
    for skill in sorted(path for path in skills.iterdir() if path.is_dir()):
        name = skill.name
        for base, rel_target in (
            (target / ".agents/skills", f"../../agentic-workspace/skills/{name}"),
            (target / ".claude/skills", f"../../agentic-workspace/skills/{name}"),
            (target / ".hermes/skills", f"../../agentic-workspace/skills/{name}"),
        ):
            link = base / name
            rel = str(link.relative_to(target))
            if ensure_link(
                link,
                rel_target,
                report,
                source=skill,
                previous_hash=previous_adapter_hashes.get(rel),
            ):
                links[rel] = rel_target
                adapter_hashes[rel] = digest_path(skill)

    agents = target / "agentic-workspace/agents"
    if not agents.exists():
        agents = PAYLOAD_ROOT / "agentic-workspace/agents"
    for source in sorted(agents.glob("*.md")):
        name, description, instructions = parse_agent(source)
        codex = target / f".codex/agents/{source.stem}.toml"
        codex_text = (
            f"name = {toml_string(name)}\n"
            f"description = {toml_string(description)}\n"
            f"developer_instructions = {toml_string(instructions)}\n"
        )
        codex_rel = str(codex.relative_to(target))
        generated_hash = write_generated_text(
            codex, codex_text, previous_generated.get(codex_rel), report
        )
        if generated_hash:
            generated_files[codex_rel] = generated_hash
        for base, rel_target in (
            (target / ".claude/agents", f"../../agentic-workspace/agents/{source.name}"),
            (target / ".hermes/agents", f"../../agentic-workspace/agents/{source.name}"),
        ):
            link = base / source.name
            rel = str(link.relative_to(target))
            if ensure_link(
                link,
                rel_target,
                report,
                source=source,
                previous_hash=previous_adapter_hashes.get(rel),
            ):
                links[rel] = rel_target
                adapter_hashes[rel] = digest_path(source)
    return links, adapter_hashes, generated_files


def merge_hook_file(path: Path, command: str, report: Report, *, claude: bool = False) -> None:
    require_contained(path, report.target, parent=True)
    if path.is_symlink():
        report.warnings.append(f"symlinked hook configuration preserved without hook merge: {display_path(path, report.target)}")
        return
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            report.warnings.append(f"invalid JSON preserved without hook merge: {display_path(path, report.target)}")
            return
    else:
        data = {}
    if not isinstance(data, dict):
        report.warnings.append(f"unexpected JSON root preserved without hook merge: {display_path(path, report.target)}")
        return
    hooks_root = data.setdefault("hooks", {})
    if not isinstance(hooks_root, dict):
        report.warnings.append(f"unexpected hooks value preserved without hook merge: {display_path(path, report.target)}")
        return
    groups = hooks_root.setdefault("PreToolUse", [])
    if not isinstance(groups, list):
        report.warnings.append(f"unexpected PreToolUse value preserved without hook merge: {display_path(path, report.target)}")
        return
    if hook_command_present(data, command):
        return
    groups.append(
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "statusMessage": "Checking commit policy",
                }
            ],
        }
    )
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n", report)


def hook_command_present(data: object, command: str) -> bool:
    if not isinstance(data, dict):
        return False
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    groups = hooks.get("PreToolUse")
    if not isinstance(groups, list):
        return False
    for group in groups:
        if not isinstance(group, dict):
            continue
        if group.get("matcher") != "Bash":
            continue
        entries = group.get("hooks")
        if not isinstance(entries, list):
            continue
        for hook in entries:
            if (
                isinstance(hook, dict)
                and hook.get("type") == "command"
                and hook.get("command") == command
            ):
                return True
    return False


def install_provider_hooks(target: Path, report: Report) -> None:
    command = provider_hook_command()
    merge_hook_file(target / ".codex/hooks.json", command, report)
    merge_hook_file(target / ".claude/settings.json", command, report, claude=True)


def provider_hook_command(platform: str | None = None) -> str:
    """Return the repository-local provider guard for the current platform.

    Provider configuration must not assume that Python is exposed under one
    particular command name. The managed launchers select an available Python
    3 runtime and propagate the guard's exit status unchanged.
    """
    platform = os.name if platform is None else platform
    if platform == "nt":
        return r"agentic-workspace\hooks\providers\commit-message-guard.cmd"
    return "./agentic-workspace/hooks/providers/commit-message-guard"


def install_git_hook(target: Path, report: Report) -> None:
    result = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        report.warnings.append("target is not a Git repository; commit-msg hook was not activated")
        return
    configured = subprocess.run(
        ["git", "-C", str(target), "config", "--local", "--get", "core.hooksPath"],
        text=True,
        capture_output=True,
    ).stdout.strip()
    expected = "agentic-workspace/hooks/git"
    if configured and configured != expected:
        report.warnings.append(
            f"existing core.hooksPath preserved: {configured}; commit guard is disconnected "
            "until that hook chain invokes agentic-workspace/hooks/git/commit-msg"
        )
        return
    if configured == expected:
        return
    if report.dry_run:
        report.updated.append(".git/config (core.hooksPath)")
        return
    subprocess.run(
        ["git", "-C", str(target), "config", "--local", "core.hooksPath", expected],
        check=True,
    )
    report.updated.append(".git/config (core.hooksPath)")


def git_toplevel(target: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        return None
    return Path(result.stdout.strip()).resolve()


def preflight_install(target: Path) -> None:
    top = git_toplevel(target)
    if top is not None and top != target:
        raise InstallError(
            f"target must be the Git worktree root ({top}), not a nested directory: {target}"
        )

    destinations = [
        target / MANIFEST,
        target / "AGENTS.md",
        target / "CLAUDE.md",
        target / "agentic-workspace/docs/repository-guide.md",
        target / "agentic-workspace/docs/imported/source.md",
        target / ".codex/hooks.json",
        target / ".claude/settings.json",
    ]
    destinations.extend(target / source.relative_to(PAYLOAD_ROOT) for source in PAYLOAD_ROOT.rglob("*") if source.is_file())
    for skill in (PAYLOAD_ROOT / "agentic-workspace/skills").iterdir():
        if skill.is_dir():
            destinations.extend(
                target / base / skill.name
                for base in (".agents/skills", ".claude/skills", ".hermes/skills")
            )
    for agent in (PAYLOAD_ROOT / "agentic-workspace/agents").glob("*.md"):
        destinations.extend(
            (
                target / ".codex/agents" / f"{agent.stem}.toml",
                target / ".claude/agents" / agent.name,
                target / ".hermes/agents" / agent.name,
            )
        )
    for destination in destinations:
        require_contained(destination, target, parent=True)

    for entry_point in (target / "AGENTS.md", target / "CLAUDE.md"):
        if entry_point.exists() and not entry_point.is_symlink() and not entry_point.is_file():
            raise InstallError(f"entry point destination is not a file: {entry_point}")


def save_manifest(
    target: Path,
    hashes: dict[str, str],
    links: dict[str, str],
    adapter_hashes: dict[str, str],
    generated_files: dict[str, str],
    entry_points: dict[str, str],
    report: Report,
    *,
    git_hook_required: bool,
) -> None:
    data = {
        "schema_version": 1,
        "product": "agentic-workspace",
        "version": __version__,
        "files": hashes,
        "links": links,
        "adapter_hashes": adapter_hashes,
        "generated_files": generated_files,
        "entry_points": entry_points,
        "git_hook_required": git_hook_required,
    }
    if report.dry_run:
        return
    path = require_contained(target / MANIFEST, target, parent=True)
    if path.is_symlink():
        raise InstallError(f"managed manifest must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary = require_contained(Path(name), target, parent=True)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        require_contained(path, target, parent=True)
        if path.is_symlink():
            raise InstallError(f"managed manifest must not be a symlink: {path}")
        os.replace(temporary, path)
        temporary = None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def install(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        raise InstallError(f"target directory does not exist: {target}")
    preflight_install(target)
    report = Report(target=target, dry_run=args.dry_run)
    previous = load_manifest(target)
    hashes = copy_payload(target, previous, report)
    entry_points = migrate_instructions(target, previous, report)
    links, adapter_hashes, generated_files = install_adapters(target, previous, report)
    install_provider_hooks(target, report)
    if not args.no_git_hook:
        install_git_hook(target, report)
    save_manifest(
        target,
        hashes,
        links,
        adapter_hashes,
        generated_files,
        entry_points,
        report,
        git_hook_required=not args.no_git_hook,
    )
    report.print()
    return 0


def adapter_specs(target: Path) -> list[tuple[Path, Path]]:
    specs: list[tuple[Path, Path]] = []
    skills = target / "agentic-workspace/skills"
    if skills.is_dir():
        for skill in sorted(path for path in skills.iterdir() if path.is_dir()):
            for base in (".agents/skills", ".claude/skills", ".hermes/skills"):
                specs.append((target / base / skill.name, skill))
    agents = target / "agentic-workspace/agents"
    if agents.is_dir():
        for source in sorted(agents.glob("*.md")):
            specs.extend(
                (
                    (target / ".claude/agents" / source.name, source),
                    (target / ".hermes/agents" / source.name, source),
                )
            )
    return specs


def adapter_matches(path: Path, source: Path) -> bool:
    if path.is_symlink():
        try:
            return path.resolve(strict=True) == source.resolve(strict=True)
        except (OSError, RuntimeError):
            return False
    return path.exists() and same_content(path, source)


def load_json_object(path: Path, target: Path) -> object | None:
    try:
        require_contained(path, target, parent=True)
    except InstallError:
        return None
    if path.is_symlink() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def git_hook_connection(target: Path) -> tuple[bool, str]:
    top = git_toplevel(target)
    if top is None:
        return True, "target is not a Git repository"
    if top != target:
        return False, f"installation target is nested below Git worktree root {top}"
    configured = subprocess.run(
        ["git", "-C", str(target), "config", "--local", "--get", "core.hooksPath"],
        text=True,
        capture_output=True,
    ).stdout.strip()
    expected = "agentic-workspace/hooks/git"
    canonical = target / "agentic-workspace/hooks/git/commit-msg"
    if configured == expected:
        if hook_is_runnable(canonical):
            return True, configured
        return False, "canonical commit-msg hook is missing or not executable"
    if not configured:
        return False, "core.hooksPath is unset"

    configured_path = Path(configured)
    if configured_path.is_absolute() or PureWindowsPath(configured).drive:
        return False, f"core.hooksPath={configured} is external and cannot be verified"
    try:
        hook_root = managed_path(target, configured)
        require_contained(hook_root, target)
    except InstallError:
        return False, f"core.hooksPath={configured} escapes the repository"
    candidates = [hook_root / "commit-msg"]
    if hook_root.name == "_":
        candidates.append(hook_root.parent / "commit-msg")
    for hook in candidates:
        if hook_invokes_canonical(hook, canonical, target):
            return True, configured
    return False, (
        f"core.hooksPath={configured} does not invoke "
        "agentic-workspace/hooks/git/commit-msg"
    )


def hook_is_runnable(path: Path, platform: str | None = None) -> bool:
    """Check hook viability using the host's execution model.

    Git for Windows executes hook scripts through its bundled shell and does
    not expose a meaningful POSIX executable bit through ``os.access``. POSIX
    hosts must still require the executable bit so Git does not ignore a hook.
    """
    if path.is_symlink() or not path.is_file():
        return False
    platform = os.name if platform is None else platform
    return platform == "nt" or os.access(path, os.X_OK)


def hook_invokes_canonical(hook: Path, canonical: Path, target: Path) -> bool:
    if not hook_is_runnable(canonical):
        return False
    if hook.is_symlink():
        try:
            return hook.resolve(strict=True) == canonical.resolve(strict=True)
        except (OSError, RuntimeError):
            return False
    if not hook_is_runnable(hook):
        return False
    text = hook.read_text(encoding="utf-8", errors="replace")
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if first_line not in {
        "#!/bin/sh",
        "#!/bin/bash",
        "#!/bin/zsh",
        "#!/usr/bin/env sh",
        "#!/usr/bin/env bash",
        "#!/usr/bin/env zsh",
    }:
        return False
    body = [
        line.strip()
        for line in text.splitlines()[1:]
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(body) != 1:
        return False
    try:
        tokens = shlex.split(body[0], comments=False, posix=True)
    except ValueError:
        return False
    relative = str(canonical.relative_to(target))
    if len(tokens) != 3 or tokens[0] != "exec" or tokens[2] not in {"$1", "$@"}:
        return False
    candidate = tokens[1].removeprefix("./")
    return candidate == relative


def check(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve()
    manifest = load_manifest(target)
    failures: list[str] = []
    if not manifest.get("files"):
        failures.append("managed manifest is missing or empty")
    for rel, expected in manifest.get("files", {}).items():
        try:
            path = managed_path(target, rel)
        except InstallError as exc:
            failures.append(str(exc))
            continue
        if path.is_symlink() or not path.is_file():
            failures.append(f"missing managed file: {rel}")
        elif digest_file(path) != expected:
            failures.append(f"modified managed file: {rel}")
    agents = target / "AGENTS.md"
    if agents.is_symlink() or not agents.is_file() or MANAGED_MARKER not in agents.read_text(encoding="utf-8"):
        failures.append("AGENTS.md is not the managed documentation entry point")
    elif manifest.get("entry_points", {}).get("AGENTS.md") and digest_file(agents) != manifest["entry_points"]["AGENTS.md"]:
        failures.append("modified managed entry point: AGENTS.md")
    claude = target / "CLAUDE.md"
    if claude.is_symlink():
        if os.readlink(claude) != "AGENTS.md" or claude.resolve(strict=False) != agents:
            failures.append("CLAUDE.md does not point to AGENTS.md")
    elif not claude.is_file():
        failures.append("CLAUDE.md compatibility entry point is missing")
    elif not agents.is_file() or not same_content(claude, agents):
        failures.append("CLAUDE.md managed copy is out of sync with AGENTS.md")

    for rel, rel_target in manifest.get("links", {}).items():
        try:
            link = managed_path(target, rel)
            source = require_contained((link.parent / rel_target).resolve(strict=False), target)
        except InstallError as exc:
            failures.append(str(exc))
            continue
        if not adapter_matches(link, source):
            failures.append(f"disconnected managed adapter: {rel}")
    for adapter, source in adapter_specs(target):
        try:
            require_contained(adapter, target, parent=True)
        except InstallError as exc:
            failures.append(str(exc))
            continue
        if not adapter_matches(adapter, source):
            failures.append(f"missing or stale provider adapter: {display_path(adapter, target)}")

    agents_dir = target / "agentic-workspace/agents"
    if agents_dir.is_dir():
        for source in sorted(agents_dir.glob("*.md")):
            name, description, instructions = parse_agent(source)
            expected_text = (
                f"name = {toml_string(name)}\n"
                f"description = {toml_string(description)}\n"
                f"developer_instructions = {toml_string(instructions)}\n"
            )
            codex = target / f".codex/agents/{source.stem}.toml"
            if codex.is_symlink() or not codex.is_file() or codex.read_text(encoding="utf-8") != expected_text:
                failures.append(f"missing or stale provider adapter: .codex/agents/{source.stem}.toml")

    command = provider_hook_command()
    for hook_path in (target / ".codex/hooks.json", target / ".claude/settings.json"):
        data = load_json_object(hook_path, target)
        if not hook_command_present(data, command):
            failures.append(f"commit policy hook is missing from {display_path(hook_path, target)}")
    if manifest.get("git_hook_required", True):
        connected, detail = git_hook_connection(target)
        if not connected:
            failures.append(
                f"Git commit guard is disconnected: {detail}; chain "
                "agentic-workspace/hooks/git/commit-msg from the existing hook"
            )
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print(f"OK: agentic-workspace {manifest.get('version')} is consistent in {target}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="agentic-workspace")
    result.add_argument("--version", action="version", version=__version__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("install", "update"):
        command = commands.add_parser(name, help=f"{name} a repository-local workspace")
        command.add_argument("target", nargs="?", default=".")
        command.add_argument("--dry-run", action="store_true")
        command.add_argument("--no-git-hook", action="store_true")
        command.set_defaults(func=install)
    command = commands.add_parser("check", help="verify an installed workspace")
    command.add_argument("target", nargs="?", default=".")
    command.set_defaults(func=check)
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        return args.func(args)
    except InstallError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
