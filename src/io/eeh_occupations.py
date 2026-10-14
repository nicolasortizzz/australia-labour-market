"""ABS EEH May 2025 — national average weekly total cash earnings by occupation (4-digit ANZSCO)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

EEH_OCCUPATION_FILE = "63060DO011_202505.xlsx"
EEH_SHEET = "Table_1"


def _parse_occupation_code(label: str) -> str | None:
    m = re.match(r"^(\d{4})\s", str(label).strip())
    return m.group(1) if m else None


def load_eeh_weekly_cash_by_occupation_4digit(raw_dir: Path) -> pd.DataFrame:
    """
    Table 1: ALL EMPLOYEES, average weekly total cash earnings — Persons column.
    Occupation labels use 4-digit ANZSCO unit groups (May 2025 EEH).
    """
    path = raw_dir / EEH_OCCUPATION_FILE
    df = pd.read_excel(path, sheet_name=EEH_SHEET, header=None)
    header_row = df.index[df.iloc[:, 1].astype(str).str.contains("AVERAGE WEEKLY", na=False)][0]
    rows: list[dict] = []
    for i in range(header_row + 2, len(df)):
        label = df.iloc[i, 0]
        if pd.isna(label) or not str(label).strip():
            continue
        code = _parse_occupation_code(str(label))
        if not code:
            continue
        persons = pd.to_numeric(df.iloc[i, 3], errors="coerce")
        if pd.isna(persons):
            continue
        rows.append(
            {
                "anzsco_4digit": code,
                "occupation_group": str(label).strip(),
                "eeh_weekly_cash_aud_national": float(persons),
            }
        )
    return pd.DataFrame(rows)


def national_eeh_all_employees_weekly(raw_dir: Path) -> float:
    """Australia total from EEH Table 9 (all employees, average weekly total cash)."""
    path = raw_dir / "63060DO001_202505.xlsx"
    t9 = pd.read_excel(path, sheet_name="Table_9", header=None)
    start = t9.index[t9.iloc[:, 0] == "AVERAGE WEEKLY TOTAL CASH EARNINGS ($)"][0] + 1
    for i in range(start, start + 15):
        if str(t9.iloc[i, 0]).strip() == "Australia":
            return float(t9.iloc[i, 1])
    raise ValueError("Australia row not found in EEH Table 9")
