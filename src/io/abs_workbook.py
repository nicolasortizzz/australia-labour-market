"""Parse ABS time-series Excel workbooks (Data1 sheet layout)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


def read_abs_data1(path: Path) -> pd.DataFrame:
    """Return wide time series: index=period (datetime), columns=series labels from row 0."""
    raw = pd.read_excel(path, sheet_name="Data1", header=None)
    if raw.empty:
        raise ValueError(f"Empty Data1 in {path}")
    labels = raw.iloc[0].tolist()
    seen: dict[str, int] = {}
    unique_labels: list = []
    for lab in labels:
        key = str(lab)
        n = seen.get(key, 0)
        seen[key] = n + 1
        unique_labels.append(key if n == 0 else f"{key}__{n}")
    body = raw.iloc[10:].copy()
    body.columns = unique_labels
    period_col = body.columns[0]
    body[period_col] = pd.to_datetime(body[period_col], errors="coerce")
    body = body.dropna(subset=[period_col]).set_index(period_col)
    for c in body.columns:
        body[c] = pd.to_numeric(body[c], errors="coerce")
    return body


def latest_value(df: pd.DataFrame, column_predicate) -> tuple[datetime, float, str]:
    """Return (period, value, column_name) for first column matching predicate."""
    cols = [c for c in df.columns if column_predicate(c)]
    if not cols:
        raise KeyError("No matching series column")
    col = cols[0]
    s = df[col].dropna()
    if s.empty:
        raise ValueError(f"No data for {col}")
    period = s.index[-1]
    return period, float(s.iloc[-1]), str(col)


def yoy_change(df: pd.DataFrame, column_predicate, months_back: int = 12) -> float | None:
    cols = [c for c in df.columns if column_predicate(c)]
    if not cols:
        return None
    col = cols[0]
    s = df[col].dropna()
    if len(s) < months_back + 1:
        return None
    latest = float(s.iloc[-1])
    prior = float(s.iloc[-1 - months_back])
    if prior == 0:
        return None
    return (latest - prior) / prior * 100.0


def match_substring(label: str, *parts: str) -> bool:
    text = str(label).lower()
    return all(p.lower() in text for p in parts)
