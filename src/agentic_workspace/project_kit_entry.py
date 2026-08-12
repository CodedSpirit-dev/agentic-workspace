"""Installed, platform-neutral entry point for the bundled Project Spec Kit."""

from __future__ import annotations

import importlib.util
from importlib.resources import as_file, files
import sys


def main() -> int:
    """Load Project Kit beside its packaged templates and execute its CLI."""
    script = files("agentic_workspace").joinpath(
        "payload",
        "agentic-workspace",
        "spec-kit",
        "scripts",
        "project_kit.py",
    )
    with as_file(script) as script_path:
        spec = importlib.util.spec_from_file_location(
            "_agentic_workspace_bundled_project_kit", script_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load bundled Project Kit from {script_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
