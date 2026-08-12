#!/usr/bin/env python3
"""Run agentic-workspace from a source checkout on any Python platform."""

from __future__ import annotations

from pathlib import Path
import sys


PRODUCT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRODUCT_ROOT / "src"))

from agentic_workspace.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
