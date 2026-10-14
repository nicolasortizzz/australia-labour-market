"""State / capital earnings comparison."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.io.earnings import load_awe_ft_adult_ordinary_by_state, load_eeh_avg_weekly_total_cash_by_state

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
    merged = awe.merge(eeh, on=["state", "capital"], how="left")
    merged.to_csv(PROC / "earnings_by_state.csv", index=False)
    merged.to_csv(TAB / "earnings_by_state.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    order = merged.sort_values("awe_weekly_aud")["state"]
    sns.barplot(
        data=merged,
        x="awe_weekly_aud",
        y="state",
        order=order,
        color="#2e7d32",
        ax=ax,
    )
    ax.set_xlabel("Average weekly earnings ($) — full-time adults, ordinary time (AWE Nov 2025)")
    ax.set_ylabel("State / territory")
    ax.set_title("AWE by state (persons, full-time adult ordinary time)")
    fig.tight_layout()
    fig.savefig(FIG / "awe_by_state.png", dpi=150)
    plt.close(fig)

    top = merged.iloc[0]
    bottom = merged.iloc[-1]
    summary = {
        "awe_reference_period": str(top["period"].date()),
        "highest_awe_state": top["state"],
        "highest_awe_weekly_aud": float(top["awe_weekly_aud"]),
        "lowest_awe_state": bottom["state"],
        "lowest_awe_weekly_aud": float(bottom["awe_weekly_aud"]),
        "highest_eeh_state": eeh.iloc[0]["state"],
        "highest_eeh_weekly_aud": float(eeh.iloc[0]["eeh_weekly_cash_aud"]),
    }
    pd.Series(summary).to_json(PROC / "earnings_summary.json", indent=2)
    return summary
