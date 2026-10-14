#!/usr/bin/env python3
"""Reproduce downloads, processing, figures, and tables."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    steps = [
        [sys.executable, "-m", "src.download.download_all"],
        [sys.executable, "-m", "src.analysis.run_analyses"],
    ]
    for cmd in steps:
        print(">>", " ".join(cmd))
        subprocess.run(cmd, cwd=ROOT, check=True)
    print("All steps complete.")


if __name__ == "__main__":
    main()
