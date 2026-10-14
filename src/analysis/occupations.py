"""Occupation demand and skilled-migration relevance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.io.jsa_ivi import load_ivi_occupation_latest
from src.io.jsa_osl import is_shortage, load_osl_2025
from src.io.skilled_lists import load_csol_codes, load_lin_19051_lists

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"


def _visa_flags(lin_lists: dict[str, set[str]], code: str) -> dict[str, bool]:
    return {k: code in lin_lists.get(k, set()) for k in ("MLTSSL", "STSOL", "ROL")}


def build_migrant_occupation_table() -> pd.DataFrame:
    osl = load_osl_2025(RAW / "jsa_occupation_shortage_list_2025.xlsx")
    csol = load_csol_codes(RAW / "homeaffairs_core_skills_occupation_list.pdf")
    lin = load_lin_19051_lists(RAW / "legislation_lin_19051_skilled_occupations.pdf")

    df = osl.merge(csol, on="anzsco", how="left")
    df["on_csol"] = df["on_csol"].fillna(False)
    for list_name in ("MLTSSL", "STSOL", "ROL"):
        codes = lin.get(list_name, set())
        df[f"on_{list_name.lower()}"] = df["anzsco"].isin(codes)

    df["is_shortage"] = df["national_rating"].apply(is_shortage)
    df["skilled_visa_relevant"] = df["on_csol"] | df["on_mltssl"] | df["on_stsol"] | df["on_rol"]
    df["migrant_priority"] = (
        df["is_shortage"].astype(int) * 2
        + df["on_csol"].astype(int) * 2
        + df["on_mltssl"].astype(int)
        + df["on_stsol"].astype(int)
    )
    return df


def run() -> dict:
    import matplotlib.pyplot as plt
    import seaborn as sns

    PROC.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    migrant = build_migrant_occupation_table()
    migrant.to_csv(PROC / "occupations_migrant_skills.csv", index=False)

    shortage_visa = migrant[migrant["is_shortage"] & migrant["skilled_visa_relevant"]].sort_values(
        ["migrant_priority", "title"],
        ascending=[False, True],
    )
    shortage_visa.head(40).to_csv(TAB / "top_shortage_skilled_visa_occupations.csv", index=False)

    ivi = load_ivi_occupation_latest(RAW / "jsa_ivi_anzsco2_states_territories_aug2025.xlsx")
    ivi.to_csv(PROC / "ivi_submajor_latest.csv", index=False)

    fig, ax = plt.subplots(figsize=(12, 8))
    top = ivi.head(12).iloc[::-1]
    ax.barh(top["title"], top["vacancies"], color="#1f4e79")
    ax.set_xlabel("Internet vacancy index (trend, Australia, latest month)")
    ax.set_title("Highest IVI occupation groups — Australia (Aug 2025)")
    fig.tight_layout()
    fig.savefig(FIG / "ivi_top_occupation_groups.png", dpi=150)
    plt.close(fig)

    summary = {
        "osl_occupations": len(migrant),
        "national_shortage_count": int(migrant["is_shortage"].sum()),
        "shortage_on_csol": int((migrant["is_shortage"] & migrant["on_csol"]).sum()),
        "shortage_on_any_skilled_list": int(
            (migrant["is_shortage"] & migrant["skilled_visa_relevant"]).sum()
        ),
        "ivi_top_group": ivi.iloc[0]["title"],
        "ivi_top_vacancies": float(ivi.iloc[0]["vacancies"]),
    }
    pd.Series(summary).to_json(PROC / "occupations_summary.json", indent=2)
    return summary
