"""ABS CPI capital city indexes (6401.0)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.io.abs_workbook import latest_value, match_substring, read_abs_data1, yoy_change

CAPITALS = [
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Adelaide",
    "Perth",
    "Hobart",
    "Darwin",
    "Canberra",
]


def load_cpi_all_groups_by_capital(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "640103.xlsx"
    df = read_abs_data1(path)
    rows: list[dict] = []
    for city in CAPITALS:
        period, value, _ = latest_value(
            df,
            lambda c, city=city: match_substring(c, "all groups cpi", city),
        )
        yoy = yoy_change(
            df,
            lambda c, city=city: match_substring(c, "all groups cpi", city),
            months_back=4,
        )
        rows.append(
            {
                "capital": city,
                "cpi_period": period,
                "cpi_all_groups_index": value,
                "cpi_yoy_pct": yoy,
            }
        )
    return pd.DataFrame(rows)


def _rent_or_housing_index(df_groups: pd.DataFrame, df_exp: pd.DataFrame, city: str) -> tuple:
    """Prefer CPI Rents (Table 9); fall back to CPI Housing (Table 5) when rents not published."""
    rent_cols = [
        c
        for c in df_exp.columns
        if match_substring(c, "rents", city)
        and "index numbers" in str(c).lower()
        and "__" not in str(c)
    ]
    if rent_cols:
        col = rent_cols[0]
        s = df_exp[col].dropna()
        period = s.index[-1]
        return period, float(s.iloc[-1]), "cpi_rents"
    period, value, _ = latest_value(
        df_groups,
        lambda c, city=city: match_substring(c, "housing", city)
        and "index numbers" in str(c).lower(),
    )
    return period, value, "cpi_housing_proxy"


def load_cpi_rents_by_capital(raw_dir: Path) -> pd.DataFrame:
    groups = read_abs_data1(raw_dir / "640103.xlsx")
    exp = read_abs_data1(raw_dir / "640107.xlsx")
    rows: list[dict] = []
    for city in CAPITALS:
        period, value, proxy = _rent_or_housing_index(groups, exp, city)
        yoy = None
        if proxy == "cpi_rents":
            yoy = yoy_change(
                exp,
                lambda c, city=city: match_substring(c, "rents", city)
                and "index numbers" in str(c).lower()
                and "__" not in str(c),
                months_back=4,
            )
        else:
            yoy = yoy_change(
                groups,
                lambda c, city=city: match_substring(c, "housing", city)
                and "index numbers" in str(c).lower(),
                months_back=4,
            )
        rows.append(
            {
                "capital": city,
                "rent_index_period": period,
                "cpi_rent_index": value,
                "rent_index_yoy_pct": yoy,
                "rent_index_source": proxy,
            }
        )
    return pd.DataFrame(rows)
