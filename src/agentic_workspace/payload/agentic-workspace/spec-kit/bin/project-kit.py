#!/usr/bin/env python3
"""Platform-neutral repository-local entry point for Project Kit."""

from __future__ import annotations

from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from project_kit import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
