"""Cost of living and rent indicators by capital city."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.io.cpi import load_cpi_all_groups_by_capital, load_cpi_rents_by_capital
from src.io.rents_observed import load_all_observed_medians
from src.io.rents_nsw import load_nsw_weekly_rents

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"


def run() -> dict:
    PROC.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    cpi = load_cpi_all_groups_by_capital(RAW)
    rents = load_cpi_rents_by_capital(RAW)
    col = cpi.merge(rents, on="capital", how="outer")
    col.to_csv(PROC / "cost_of_living_by_capital.csv", index=False)
    col.to_csv(TAB / "cost_of_living_by_capital.csv", index=False)

    nsw_rent = load_nsw_weekly_rents(RAW / "nsw_rental_bond_lodgements_nov2025.xlsx")
    nsw_rent.to_csv(PROC / "nsw_median_rent_nov2025.csv", index=False)
    try:
        observed = load_all_observed_medians(RAW)
        observed.to_csv(PROC / "median_weekly_rents_observed.csv", index=False)
    except FileNotFoundError:
        observed = None

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    cpi_sorted = col.sort_values("cpi_all_groups_index")
    axes[0].barh(cpi_sorted["capital"], cpi_sorted["cpi_all_groups_index"], color="#6a1b9a")
    axes[0].set_title("CPI all groups index (latest quarter)")
    axes[0].set_xlabel("Index (ABS CPI, capital city)")

    rent_sorted = col.sort_values("cpi_rent_index")
    axes[1].barh(rent_sorted["capital"], rent_sorted["cpi_rent_index"], color="#c62828")
    axes[1].set_title("CPI rents component index (latest quarter)")
    axes[1].set_xlabel("Index (ABS CPI rents, capital city)")
    fig.suptitle("Cost of living proxies by capital city")
    fig.tight_layout()
    fig.savefig(FIG / "cpi_and_rents_by_capital.png", dpi=150)
    plt.close(fig)

    highest_cpi = col.loc[col["cpi_all_groups_index"].idxmax()]
    lowest_cpi = col.loc[col["cpi_all_groups_index"].idxmin()]
    summary = {
        "cpi_highest_capital": highest_cpi["capital"],
        "cpi_highest_index": float(highest_cpi["cpi_all_groups_index"]),
        "cpi_lowest_capital": lowest_cpi["capital"],
        "cpi_lowest_index": float(lowest_cpi["cpi_all_groups_index"]),
        "nsw_median_weekly_rent_aud": float(
            nsw_rent.loc[nsw_rent["metric"] == "median_weekly_rent_aud", "value"].iloc[0]
        ),
        "capitals_with_observed_rent": int(observed.shape[0]) if observed is not None else 0,
    }
    pd.Series(summary).to_json(PROC / "col_summary.json", indent=2)
    return summary
