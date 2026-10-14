"""
Affordability index: earnings vs cost of living.

Methodology (documented in README):
- Base index A: real_earnings_index = (weekly AWE / CPI all-groups index) × 100.
  Higher = more weekly pay per unit of city price level (purchasing-power proxy).
- Base index B: rent_burden_pct = 100 × (imputed_weekly_rent / weekly AWE).
  Lower = more affordable housing relative to pay.

Imputed weekly rent by capital (when bond data unavailable):
  rent_hat(city) = NSW_median_rent × (CPI_rent_index(city) / CPI_rent_index(Sydney))
  Anchored to NSW Fair Trading Nov 2025 median; other cities scaled by ABS CPI rents only.

Sensitivity (saved separately):
- S1: use EEH average weekly total cash instead of AWE ordinary time.
- S2: rent burden using CPI all-groups index instead of CPI rents for scaling.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.io.cpi import load_cpi_all_groups_by_capital, load_cpi_rents_by_capital
from src.io.earnings import load_awe_ft_adult_ordinary_by_state, load_eeh_avg_weekly_total_cash_by_state
from src.io.rents_nsw import load_nsw_weekly_rents

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"


def _impute_weekly_rents(cpi_rents: pd.DataFrame, nsw_median: float) -> pd.DataFrame:
    sydney_idx = float(
        cpi_rents.loc[cpi_rents["capital"] == "Sydney", "cpi_rent_index"].iloc[0]
    )
    out = cpi_rents.copy()
    out["imputed_median_weekly_rent_aud"] = nsw_median * (out["cpi_rent_index"] / sydney_idx)
    out["rent_imputation"] = "NSW bond median × (city CPI rent / Sydney CPI rent)"
    return out


def run() -> dict:
    PROC.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    awe = load_awe_ft_adult_ordinary_by_state(RAW)
    eeh = load_eeh_avg_weekly_total_cash_by_state(RAW)
    cpi = load_cpi_all_groups_by_capital(RAW)
    cpi_rent = load_cpi_rents_by_capital(RAW)
    nsw_median = float(
        load_nsw_weekly_rents(RAW / "nsw_rental_bond_lodgements_nov2025.xlsx")
        .loc[lambda d: d["metric"] == "median_weekly_rent_aud", "value"]
        .iloc[0]
    )

    rents = _impute_weekly_rents(cpi_rent, nsw_median)
    base = awe.merge(cpi, left_on="capital", right_on="capital", how="left")
    base = base.merge(
        rents[["capital", "imputed_median_weekly_rent_aud", "rent_imputation"]],
        on="capital",
        how="left",
    )
    base["real_earnings_index"] = base["awe_weekly_aud"] / base["cpi_all_groups_index"] * 100.0
    base["rent_burden_pct"] = (
        base["imputed_median_weekly_rent_aud"] / base["awe_weekly_aud"] * 100.0
    )
    base["residual_weekly_aud"] = base["awe_weekly_aud"] - base["imputed_median_weekly_rent_aud"]
    base = base.sort_values("real_earnings_index", ascending=False)
    base.to_csv(PROC / "affordability_base.csv", index=False)
    base.to_csv(TAB / "affordability_index.csv", index=False)

    # Sensitivity
    s1 = base.merge(eeh, on=["state", "capital"], how="left")
    s1["real_earnings_index_s1"] = s1["eeh_weekly_cash_aud"] / s1["cpi_all_groups_index"] * 100.0
    s1["rent_burden_pct_s1"] = s1["imputed_median_weekly_rent_aud"] / s1["eeh_weekly_cash_aud"] * 100.0

    sydney_cpi = float(cpi.loc[cpi["capital"] == "Sydney", "cpi_all_groups_index"].iloc[0])
    rent_s2 = nsw_median * (cpi["cpi_all_groups_index"] / sydney_cpi)
    rent_s2 = cpi[["capital"]].assign(imputed_rent_s2=rent_s2.values)
    s2 = base.merge(rent_s2, on="capital", how="left")
    s2["rent_burden_pct_s2"] = s2["imputed_rent_s2"] / s2["awe_weekly_aud"] * 100.0
    sens = s1.merge(s2[["state", "rent_burden_pct_s2"]], on="state", how="left")[
        [
            "state",
            "capital",
            "real_earnings_index",
            "real_earnings_index_s1",
            "rent_burden_pct",
            "rent_burden_pct_s1",
            "rent_burden_pct_s2",
        ]
    ]
    sens.to_csv(TAB / "affordability_sensitivity.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    plot_df = base.sort_values("real_earnings_index")
    ax.scatter(
        plot_df["cpi_all_groups_index"],
        plot_df["awe_weekly_aud"],
        s=120,
        c=plot_df["rent_burden_pct"],
        cmap="RdYlGn_r",
        edgecolors="k",
    )
    for _, row in plot_df.iterrows():
        ax.annotate(row["state"], (row["cpi_all_groups_index"], row["awe_weekly_aud"]), fontsize=9)
    ax.set_xlabel("CPI all groups index (capital)")
    ax.set_ylabel("AWE weekly ($, FT adult ordinary time)")
    ax.set_title("Affordability map — colour = imputed rent burden (% of AWE)")
    fig.colorbar(ax.collections[0], ax=ax, label="Rent burden %")
    fig.tight_layout()
    fig.savefig(FIG / "affordability_scatter.png", dpi=150)
    plt.close(fig)

    best = base.iloc[0]
    worst_burden = base.loc[base["rent_burden_pct"].idxmax()]
    summary = {
        "best_real_earnings_capital": best["capital"],
        "best_real_earnings_state": best["state"],
        "best_real_earnings_index": float(best["real_earnings_index"]),
        "highest_rent_burden_capital": worst_burden["capital"],
        "highest_rent_burden_pct": float(worst_burden["rent_burden_pct"]),
        "nsw_anchor_median_rent_aud": nsw_median,
    }
    pd.Series(summary).to_json(PROC / "affordability_summary.json", indent=2)
    return summary
