"""ABS Average Weekly Earnings (6302.0) — state Table 11 trend series."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.download.config import AWE_STATE_FILES, STATE_TO_CAPITAL
from src.io.abs_workbook import latest_value, match_substring, read_abs_data1, yoy_change

STATE_FILE_PREFIX = {st: f"awe_{st.lower()}_" for st in AWE_STATE_FILES}


def awe_state_path(raw_dir: Path, state: str) -> Path:
    fname = AWE_STATE_FILES[state]
    return raw_dir / f"awe_{state.lower()}_{fname}"


def load_awe_ft_adult_ordinary_by_state(raw_dir: Path) -> pd.DataFrame:
    """Latest AWE: persons, full-time, adult, ordinary time earnings ($/week) by state."""
    rows: list[dict] = []
    for state in AWE_STATE_FILES:
        path = awe_state_path(raw_dir, state)
        df = read_abs_data1(path)
        period, value, col = latest_value(
            df,
            lambda c: match_substring(c, "persons", "full time", "adult", "ordinary time"),
        )
        yoy = yoy_change(
            df,
            lambda c: match_substring(c, "persons", "full time", "adult", "ordinary time"),
            months_back=12,
        )
        rows.append(
            {
                "state": state,
                "capital": STATE_TO_CAPITAL[state],
                "period": period,
                "awe_weekly_aud": value,
                "awe_yoy_pct": yoy,
            }
        )
    out = pd.DataFrame(rows).sort_values("awe_weekly_aud", ascending=False)
    return out


def load_eeh_avg_weekly_total_cash_by_state(raw_dir: Path) -> pd.DataFrame:
    """EEH May 2025 Table 9 — all employees, average weekly total cash earnings by state."""
    path = raw_dir / "63060DO001_202505.xlsx"
    t9 = pd.read_excel(path, sheet_name="Table_9", header=None)
    start = t9.index[t9.iloc[:, 0] == "AVERAGE WEEKLY TOTAL CASH EARNINGS ($)"][0] + 1
    rows: list[dict] = []
    state_map = {
        "New South Wales": "NSW",
        "Victoria": "VIC",
        "Queensland": "QLD",
        "South Australia": "SA",
        "Western Australia": "WA",
        "Tasmania": "TAS",
        "Northern Territory": "NT",
        "Australian Capital Territory": "ACT",
    }
    for i in range(start, start + 10):
        label = t9.iloc[i, 0]
        if label not in state_map:
            continue
        st = state_map[label]
        val = float(t9.iloc[i, 1])
        rows.append(
            {
                "state": st,
                "capital": STATE_TO_CAPITAL[st],
                "eeh_weekly_cash_aud": val,
            }
        )
    return pd.DataFrame(rows).sort_values("eeh_weekly_cash_aud", ascending=False)
