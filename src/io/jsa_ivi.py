from __future__ import annotations

from pathlib import Path

import pandas as pd

STATE_CODES = {
    "1": "NSW",
    "2": "VIC",
    "3": "QLD",
    "4": "SA",
    "5": "WA",
    "6": "TAS",
    "7": "NT",
    "8": "ACT",
}


def load_ivi_trend_national(path: Path) -> pd.DataFrame:
    """National vacancy counts from Trend sheet (ANZSCO rows, Australia total columns)."""
    df = pd.read_excel(path, sheet_name="Trend")
    date_cols = [c for c in df.columns if isinstance(c, pd.Timestamp) or "20" in str(c)]
    meta = df[["ANZSCO_CODE", "OCCUPATION_TITLE"]].copy()
    meta.columns = ["anzsco", "title"]
    meta["anzsco"] = meta["anzsco"].astype(str).str.replace(r"\.0$", "", regex=True)
    aus_cols = [c for c in date_cols if "Australia" in str(c)]
    if not aus_cols:
        national_row = df[df["ANZSCO_CODE"] == 0]
        if national_row.empty:
            national_row = df[df["Level"] == 1].head(1)
        values = national_row[date_cols].iloc[0]
        out = pd.DataFrame({"period": pd.to_datetime(date_cols), "vacancies": values.values})
        return out.dropna()
    raise NotImplementedError("Unexpected IVI column layout")


def _date_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if hasattr(c, "year")]


def load_ivi_occupation_latest(path: Path, state: str = "AUST") -> pd.DataFrame:
    """Latest month IVI vacancies by ANZSCO sub-major group (Level 3), national or by state."""
    df = pd.read_excel(path, sheet_name="Trend")
    date_cols = _date_columns(df)
    if not date_cols:
        raise ValueError("No date columns in IVI Trend sheet")
    latest_col = sorted(date_cols)[-1]
    sub = df[(df["Level"] == 3) & (df["State"] == state)].copy()
    sub["anzsco"] = sub["ANZSCO_CODE"].astype(str).str.replace(r"\.0$", "", regex=True)
    sub["vacancies"] = pd.to_numeric(sub[latest_col], errors="coerce")
    sub["title"] = sub["Title"]
    out = sub[["anzsco", "title", "vacancies"]].dropna(subset=["vacancies"])
    if len(date_cols) >= 13:
        prior_col = date_cols[-13]
        prior = pd.to_numeric(sub[prior_col], errors="coerce")
        out["vacancy_yoy_pct"] = (out["vacancies"] - prior) / prior * 100.0
    return out.sort_values("vacancies", ascending=False).reset_index(drop=True)


def load_ivi_group_by_state(path: Path, anzsco2: str) -> pd.DataFrame:
    """Latest IVI vacancies for one ANZSCO2 sub-major group across states."""
    df = pd.read_excel(path, sheet_name="Trend")
    date_cols = _date_columns(df)
    latest_col = sorted(date_cols)[-1]
    sub = df[(df["Level"] == 3) & (df["ANZSCO_CODE"].astype(str) == str(anzsco2))].copy()
    sub["vacancies"] = pd.to_numeric(sub[latest_col], errors="coerce")
    state_map = {
        "NSW": "NSW",
        "VIC": "VIC",
        "QLD": "QLD",
        "SA": "SA",
        "WA": "WA",
        "TAS": "TAS",
        "NT": "NT",
        "ACT": "ACT",
        "AUST": "AUST",
    }
    rows = []
    for st in state_map:
        row = sub[sub["State"] == st]
        if row.empty:
            continue
        rows.append({"state": st, "ivi_vacancies": float(row["vacancies"].iloc[0])})
    return pd.DataFrame(rows)
