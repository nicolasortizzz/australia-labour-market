"""NSW Fair Trading rental bond lodgement statistics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_nsw_weekly_rents(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Nov 25 Rental Bond Lodgments", header=2)
    rent = pd.to_numeric(df["Weekly Rent"], errors="coerce")
    clean = rent[(rent >= 50) & (rent <= 5000)]
    return pd.DataFrame(
        {
            "metric": ["median_weekly_rent_aud", "mean_weekly_rent_aud", "n_lodgements"],
            "value": [float(clean.median()), float(clean.mean()), int(clean.notna().sum())],
        }
    )
