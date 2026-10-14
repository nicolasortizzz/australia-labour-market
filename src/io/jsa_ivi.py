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
    # National total is typically the rightmost date block under 'Australia' — use max across state cols for row 0
    # For occupation rows, sum isn't correct; use Australia if present in column name
    aus_cols = [c for c in date_cols if "Australia" in str(c)]
    if not aus_cols:
        # IVI file: date columns are plain timestamps; national row Level=1 ANZSCO 0
        national_row = df[df["ANZSCO_CODE"] == 0]
        if national_row.empty:
            national_row = df[df["Level"] == 1].head(1)
        values = national_row[date_cols].iloc[0]
        out = pd.DataFrame({"period": pd.to_datetime(date_cols), "vacancies": values.values})
        return out.dropna()
    raise NotImplementedError("Unexpected IVI column layout")


def load_ivi_occupation_latest(path: Path) -> pd.DataFrame:
    """Latest month vacancies by 4-digit ANZSCO unit group (national aggregate column)."""
    df = pd.read_excel(path, sheet_name="Trend")
    date_cols = [c for c in df.columns if isinstance(c, (pd.Timestamp,))]
    if not date_cols:
        date_cols = [
            c
            for c in df.columns
            if hasattr(c, "year") or (isinstance(c, str) and c[:4].isdigit())
        ]
    latest_col = sorted(date_cols)[-1]
    sub = df[df["Level"] == 3].copy()  # 4-digit unit groups
    sub["anzsco"] = sub["ANZSCO_CODE"].astype(str).str.replace(r"\.0$", "", regex=True)
    sub["vacancies"] = pd.to_numeric(sub[latest_col], errors="coerce")
    sub["title"] = sub["OCCUPATION_TITLE"]
    out = sub[["anzsco", "title", "vacancies"]].dropna(subset=["vacancies"])
    # YoY: compare to column 12 months earlier if available
    if len(date_cols) >= 13:
        prior_col = date_cols[-13]
        sub["vacancies_prior"] = pd.to_numeric(sub[prior_col], errors="coerce")
        out["vacancy_yoy_pct"] = (
            (out["vacancies"] - sub["vacancies_prior"]) / sub["vacancies_prior"] * 100
        )
    return out.sort_values("vacancies", ascending=False)
