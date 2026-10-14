from __future__ import annotations

from pathlib import Path

import pandas as pd

SHORTAGE_SHEET = "2025 OSL (ANZSCO 2022)"


def load_osl_2025(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=SHORTAGE_SHEET, header=7)
    df = df.rename(
        columns={
            "Occupation code (ANZSCO 2022)": "anzsco",
            "Occupation title": "title",
            "NS - No Shortage\nS - Shortage\nR - Regional Shortage\nM - Metro Shortage": "national_rating",
        }
    )
    df["anzsco"] = df["anzsco"].astype(str).str.replace(r"\.0$", "", regex=True)
    state_cols = [c for c in df.columns if c in ("NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT")]
    keep = ["anzsco", "title", "national_rating"] + state_cols
    return df[keep].dropna(subset=["anzsco"])


def is_shortage(rating: str) -> bool:
    return str(rating).strip().upper() in {"S", "R", "M"}
