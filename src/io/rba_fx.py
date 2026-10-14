"""RBA Table F11 — indicative AUD/USD (A$1=USD) monthly series."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_F11_PATH = ROOT / "data" / "raw" / "rba_f11_exchange_rates.csv"


def load_f11_aud_usd_series(path: Path = DEFAULT_F11_PATH) -> pd.DataFrame:
    """Parse RBA F11 CSV; return date + aud_usd columns sorted by date."""
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[tuple[str, float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"\d{2}-[A-Za-z]{3}-\d{4},", line):
            continue
        parts = line.split(",")
        rate = pd.to_numeric(parts[1], errors="coerce")
        if pd.isna(rate):
            continue
        rows.append((parts[0], float(rate)))
    if not rows:
        raise ValueError(f"No AUD/USD observations in {path}")
    df = pd.DataFrame(rows, columns=["rate_date", "aud_usd"])
    df["rate_date_parsed"] = pd.to_datetime(df["rate_date"], format="%d-%b-%Y")
    return df.sort_values("rate_date_parsed").reset_index(drop=True)


def latest_aud_usd(path: Path = DEFAULT_F11_PATH) -> dict[str, str | float]:
    """Latest available F11 AUD/USD observation (one USD per one AUD)."""
    series = load_f11_aud_usd_series(path)
    last = series.iloc[-1]
    return {
        "aud_usd": float(last["aud_usd"]),
        "rate_date": str(last["rate_date"]),
    }
