"""Merge analysis summaries into a single JSON for README generation."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"


def run() -> dict:
    keys = [
        "occupations_summary.json",
        "earnings_summary.json",
        "col_summary.json",
        "affordability_summary.json",
        "savings_summary.json",
    ]
    merged: dict = {}
    for name in keys:
        path = PROC / name
        if path.is_file():
            merged.update(json.loads(path.read_text(encoding="utf-8")))
    out = PROC / "project_findings.json"
    out.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged
