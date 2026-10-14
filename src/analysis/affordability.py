"""
Affordability index: earnings vs cost of living.

Methodology (documented in README):
- Base index A: real_earnings_index = (weekly AWE / CPI all-groups index) × 100.
  Higher = more weekly pay per unit of city price level (purchasing-power proxy).
- Base index B: rent_burden_pct = 100 × (median_weekly_rent / weekly AWE).
  Lower = more affordable housing relative to pay.

Median weekly rent by capital:
  Prefer official bond / rental-report medians where downloaded (see `rent_observed`).
  Fallback: NSW_median × (CPI_rent_index(city) / CPI_rent_index(Sydney)) for ACT and NT.

Sensitivity (saved separately):
- S1: use EEH average weekly total cash instead of AWE ordinary time.
- S2: rent burden using CPI all-groups index instead of CPI rents for scaling (imputation only).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from matplotlib.ticker import FuncFormatter

from src.fx import add_usd_columns, aud_usd_rate, matplotlib_aud_usd_formatter
from src.io.cpi import load_cpi_all_groups_by_capital, load_cpi_rents_by_capital
from src.io.earnings import load_awe_ft_adult_ordinary_by_state, load_eeh_avg_weekly_total_cash_by_state
from src.io.rents_merge import merge_observed_and_imputed
from src.io.rents_nsw import load_nsw_weekly_rents
from src.io.rents_observed import load_all_observed_medians

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

    awe = load_awe_ft_adult_ordinary_by_state(RAW)
    eeh = load_eeh_avg_weekly_total_cash_by_state(RAW)
    cpi = load_cpi_all_groups_by_capital(RAW)
    cpi_rent = load_cpi_rents_by_capital(RAW)
    nsw_median = float(
        load_nsw_weekly_rents(RAW / "nsw_rental_bond_lodgements_nov2025.xlsx")
        .loc[lambda d: d["metric"] == "median_weekly_rent_aud", "value"]
        .iloc[0]
    )

    observed = load_all_observed_medians(RAW)
    observed = add_usd_columns(observed, ["median_weekly_rent_aud"])
    observed.to_csv(PROC / "median_weekly_rents_observed.csv", index=False)
    observed.to_csv(TAB / "median_weekly_rents_by_capital.csv", index=False)

    rents = merge_observed_and_imputed(cpi_rent, observed, nsw_median)
    base = awe.merge(cpi, left_on="capital", right_on="capital", how="left")
    base = base.merge(
        rents[
            [
                "capital",
                "median_weekly_rent_aud",
                "rent_observed",
                "rent_imputation",
                "rent_source",
                "period_label",
            ]
        ],
        on="capital",
        how="left",
    )
    base = base.rename(columns={"period_label": "rent_period"})
    base["real_earnings_index"] = base["awe_weekly_aud"] / base["cpi_all_groups_index"] * 100.0
    base["rent_burden_pct"] = (
        base["median_weekly_rent_aud"] / base["awe_weekly_aud"] * 100.0
    )
    base["residual_weekly_aud"] = base["awe_weekly_aud"] - base["median_weekly_rent_aud"]
    base = base.sort_values("real_earnings_index", ascending=False)
    base = add_usd_columns(
        base, ["awe_weekly_aud", "median_weekly_rent_aud", "residual_weekly_aud"]
    )
    base.to_csv(PROC / "affordability_base.csv", index=False)
    base.to_csv(TAB / "affordability_index.csv", index=False)

    # Sensitivity
    s1 = base.merge(eeh, on=["state", "capital"], how="left")
    s1["real_earnings_index_s1"] = s1["eeh_weekly_cash_aud"] / s1["cpi_all_groups_index"] * 100.0
    s1["rent_burden_pct_s1"] = s1["median_weekly_rent_aud"] / s1["eeh_weekly_cash_aud"] * 100.0

    sydney_cpi = float(cpi.loc[cpi["capital"] == "Sydney", "cpi_all_groups_index"].iloc[0])
    rent_s2 = nsw_median * (cpi["cpi_all_groups_index"] / sydney_cpi)
    rent_s2 = cpi[["capital"]].assign(imputed_rent_s2=rent_s2.values)
    s2 = base.merge(rent_s2, on="capital", how="left")
    s2["rent_burden_pct_s2"] = s2.apply(
        lambda r: (
            r["median_weekly_rent_aud"] / r["awe_weekly_aud"] * 100.0
            if r["rent_observed"]
            else r["imputed_rent_s2"] / r["awe_weekly_aud"] * 100.0
        ),
        axis=1,
    )
    sens = s1.merge(s2[["state", "rent_burden_pct_s2"]], on="state", how="left")[
        [
            "state",
            "capital",
            "rent_observed",
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
        marker = "●" if row["rent_observed"] else "○"
        ax.annotate(
            f"{row['state']}{marker}",
            (row["cpi_all_groups_index"], row["awe_weekly_aud"]),
            fontsize=9,
        )
    ax.set_xlabel("CPI all groups index (capital)")
    fx_rate = aud_usd_rate()
    ax.yaxis.set_major_formatter(FuncFormatter(matplotlib_aud_usd_formatter(fx_rate, decimals=0)))
    ax.set_ylabel("AWE weekly (AUD, USD in parentheses); FT adult ordinary time")
    ax.set_title("Affordability map — colour = rent burden (% of AWE); ● observed rent, ○ imputed")
    fig.colorbar(ax.collections[0], ax=ax, label="Rent burden %")
    fig.tight_layout()
    fig.savefig(FIG / "affordability_scatter.png", dpi=150)
    plt.close(fig)

    best = base.iloc[0]
    worst_burden = base.loc[base["rent_burden_pct"].idxmax()]
    n_observed = int(base["rent_observed"].sum())
    summary = {
        "best_real_earnings_capital": best["capital"],
        "best_real_earnings_state": best["state"],
        "best_real_earnings_index": float(best["real_earnings_index"]),
        "highest_rent_burden_capital": worst_burden["capital"],
        "highest_rent_burden_pct": float(worst_burden["rent_burden_pct"]),
        "capitals_with_observed_rent": n_observed,
        "nsw_anchor_median_rent_aud": nsw_median,
    }
    pd.Series(summary).to_json(PROC / "affordability_summary.json", indent=2)
    return summary
