"""
Where can you save the most? — occupation-specific disposable savings by capital.

Earnings: ABS EEH May 2025 national occupation weekly cash (4-digit ANZSCO), scaled to
states using EEH Table 9 state / Australia relativities (flagged estimate).

Tax: ATO 2025–26 resident rates + 2% Medicare levy (super excluded).

Rent: observed medians + scenario rents (see src/io/rent_scenarios.py).

Other living costs: HES 2015-16 lone-person non-housing anchor, CPI-scaled (low/central/high).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.analysis.professional_profiles import PROFESSIONAL_PROFILES, ProfessionalProfile
from src.download.config import STATE_TO_CAPITAL
from src.io.ato_tax import ATO_TAX_RATES_URL, INCOME_YEAR, after_tax_weekly_cash
from src.io.earnings import load_eeh_avg_weekly_total_cash_by_state
from src.io.eeh_occupations import load_eeh_weekly_cash_by_occupation_4digit, national_eeh_all_employees_weekly
from src.io.jsa_ivi import load_ivi_group_by_state
from src.io.jsa_osl import load_osl_2025
from src.io.living_costs import load_non_rent_living_costs_by_capital
from src.io.rent_scenarios import build_rent_scenarios
from src.io.skilled_lists import load_csol_codes, load_lin_19051_lists

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"


def _visa_pathway_notes(on_csol: bool, on_mltssl: bool, on_stsol: bool, on_rol: bool) -> str:
    parts: list[str] = []
    if on_csol:
        parts.append("CSOL (Core Skills Occupation List) — Skills in Demand / employer-sponsored pathways")
    if on_mltssl:
        parts.append("MLTSSL — skilled independent (189) / state nominated (190/491) subject to points and caps")
    if on_stsol:
        parts.append("STSOL — may be eligible for 190/491 depending on state lists; check current state nominations")
    if on_rol:
        parts.append("ROL — regional employer-sponsored and some 491 streams")
    if not parts:
        parts.append("Not on downloaded CSOL/MLTSSL/STSOL/ROL lists — verify eligibility on immi.homeaffairs.gov.au")
    return "; ".join(parts) + ". Rules change frequently — confirm on Home Affairs."


def _occupation_meta(raw_dir: Path) -> pd.DataFrame:
    osl = load_osl_2025(raw_dir / "jsa_occupation_shortage_list_2025.xlsx")
    csol = load_csol_codes(raw_dir / "homeaffairs_core_skills_occupation_list.pdf")
    lin = load_lin_19051_lists(raw_dir / "legislation_lin_19051_skilled_occupations.pdf")
    ivi_path = raw_dir / "jsa_ivi_anzsco2_states_territories_aug2025.xlsx"

    rows: list[dict] = []
    for p in PROFESSIONAL_PROFILES:
        if p.anzsco == "2222":
            osl_row = osl[osl["anzsco"] == "222211"]
            lookup_code = "222211"
        else:
            osl_row = osl[osl["anzsco"] == p.anzsco]
            lookup_code = p.anzsco
        national_rating = osl_row["national_rating"].iloc[0] if len(osl_row) else "N/A"
        on_csol = lookup_code in set(csol["anzsco"])
        on_mltssl = lookup_code in lin.get("MLTSSL", set())
        on_stsol = lookup_code in lin.get("STSOL", set())
        on_rol = lookup_code in lin.get("ROL", set())

        ivi_nat = load_ivi_group_by_state(ivi_path, p.ivi_anzsco2)
        ivi_aust = float(ivi_nat.loc[ivi_nat["state"] == "AUST", "ivi_vacancies"].iloc[0])

        rows.append(
            {
                "anzsco": p.anzsco,
                "title": p.title,
                "eeh_anzsco_4digit": p.eeh_anzsco_4digit,
                "eeh_occupation_label": p.eeh_occupation_label,
                "earnings_source_note": p.earnings_note,
                "osl_national_rating": national_rating,
                "on_csol": on_csol,
                "on_mltssl": on_mltssl,
                "on_stsol": on_stsol,
                "on_rol": on_rol,
                "ivi_anzsco2": p.ivi_anzsco2,
                "ivi_group_title": p.ivi_group_title,
                "ivi_vacancies_australia_aug2025": ivi_aust,
                "visa_pathway_notes": _visa_pathway_notes(on_csol, on_mltssl, on_stsol, on_rol),
            }
        )
    return pd.DataFrame(rows)


def _state_weekly_occupation_earnings(
    occ_4digit: str, eeh_occ: pd.DataFrame, eeh_states: pd.DataFrame, national_total: float
) -> pd.DataFrame:
    nat_occ = float(
        eeh_occ.loc[eeh_occ["anzsco_4digit"] == occ_4digit, "eeh_weekly_cash_aud_national"].iloc[0]
    )
    eeh_states = eeh_states.copy()
    eeh_states["state_relativity"] = eeh_states["eeh_weekly_cash_aud"] / national_total
    eeh_states["weekly_gross_aud"] = nat_occ * eeh_states["state_relativity"]
    eeh_states["earnings_is_state_estimate"] = True
    eeh_states["earnings_method"] = (
        "EEH May 2025 national 4-digit occupation weekly cash × "
        "(state EEH Table 9 / Australia EEH Table 9)"
    )
    return eeh_states


def run() -> dict:
    PROC.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    eeh_occ = load_eeh_weekly_cash_by_occupation_4digit(RAW)
    eeh_occ.to_csv(PROC / "eeh_occupation_weekly_cash_national.csv", index=False)
    national_eeh = national_eeh_all_employees_weekly(RAW)
    eeh_states = load_eeh_avg_weekly_total_cash_by_state(RAW)
    living = load_non_rent_living_costs_by_capital(RAW)
    rents = build_rent_scenarios(RAW)
    rents.to_csv(PROC / "rent_scenarios_by_capital.csv", index=False)
    rents.to_csv(TAB / "rent_scenarios_by_capital.csv", index=False)

    meta = _occupation_meta(RAW)
    meta.to_csv(TAB / "professional_occupations_visa_demand.csv", index=False)

    detail_rows: list[dict] = []
    for p in PROFESSIONAL_PROFILES:
        earn = _state_weekly_occupation_earnings(
            p.eeh_anzsco_4digit, eeh_occ, eeh_states, national_eeh
        )
        for _, st in earn.iterrows():
            cap = st["capital"]
            gross_weekly = float(st["weekly_gross_aud"])
            tax = after_tax_weekly_cash(gross_weekly * 52.0)
            liv = living.loc[living["capital"] == cap].iloc[0]
            for _, rent_row in rents[rents["capital"] == cap].iterrows():
                for col_sens, sens in [
                    ("non_rent_living_weekly_low_aud", "low"),
                    ("non_rent_living_weekly_central_aud", "central"),
                    ("non_rent_living_weekly_high_aud", "high"),
                ]:
                    other = float(liv[col_sens])
                    rent = float(rent_row["weekly_rent_aud"])
                    disposable = tax["net_weekly_aud"] - rent - other
                    detail_rows.append(
                        {
                            "anzsco": p.anzsco,
                            "title": p.title,
                            "state": st["state"],
                            "capital": cap,
                            "eeh_anzsco_4digit": p.eeh_anzsco_4digit,
                            "weekly_gross_aud": gross_weekly,
                            "weekly_net_after_tax_aud": tax["net_weekly_aud"],
                            "effective_tax_rate_pct": tax["effective_tax_rate_pct"],
                            "tax_income_year": INCOME_YEAR,
                            "tax_source_url": ATO_TAX_RATES_URL,
                            "earnings_is_state_estimate": True,
                            "rent_scenario": rent_row["rent_scenario"],
                            "weekly_rent_aud": rent,
                            "rent_scenario_note": rent_row["rent_scenario_note"],
                            "living_cost_sensitivity": sens,
                            "weekly_other_living_aud": other,
                            "disposable_savings_weekly_aud": disposable,
                            "disposable_savings_annual_aud": disposable * 52.0,
                        }
                    )

    detail = pd.DataFrame(detail_rows)
    detail.to_csv(PROC / "savings_by_city_detail.csv", index=False)
    detail.to_csv(TAB / "savings_by_city_detail.csv", index=False)

    central = detail[
        (detail["living_cost_sensitivity"] == "central")
        & (detail["rent_scenario"] == "alone_all_median")
    ].copy()
    central["rank_within_occupation"] = central.groupby("anzsco")["disposable_savings_weekly_aud"].rank(
        ascending=False, method="dense"
    )
    rank_tbl = central.sort_values(["anzsco", "rank_within_occupation"])[
        [
            "anzsco",
            "title",
            "capital",
            "weekly_gross_aud",
            "weekly_net_after_tax_aud",
            "weekly_rent_aud",
            "weekly_other_living_aud",
            "disposable_savings_weekly_aud",
            "rank_within_occupation",
        ]
    ]
    rank_tbl.to_csv(TAB / "savings_rankings_alone_median_central.csv", index=False)

    # Chart: top occupation (Accountant general) — alone all median, central living costs
    chart_occ = "221111"
    plot_df = central[central["anzsco"] == chart_occ].sort_values("disposable_savings_weekly_aud")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(plot_df["capital"], plot_df["disposable_savings_weekly_aud"], color="#2e7d32")
    ax.axvline(0, color="k", linewidth=0.8)
    ax.set_xlabel("Disposable savings ($/week, after tax, rent, other living costs)")
    ax.set_title(
        f"Where to save most — {plot_df['title'].iloc[0]} (ANZSCO {chart_occ})\n"
        "Rent: all-dwellings median; living costs: central HES/CPI scenario"
    )
    fig.tight_layout()
    fig.savefig(FIG / "savings_by_city_accountant_alone_median.png", dpi=150)
    plt.close(fig)

    # Facet-style chart: best capital per occupation (central, alone_all_median)
    best = central.loc[central.groupby("anzsco")["disposable_savings_weekly_aud"].idxmax()]
    fig, ax = plt.subplots(figsize=(11, 7))
    best_sorted = best.sort_values("disposable_savings_weekly_aud")
    ax.barh(best_sorted["title"], best_sorted["disposable_savings_weekly_aud"], color="#1565c0")
    for i, row in enumerate(best_sorted.itertuples()):
        ax.text(
            row.disposable_savings_weekly_aud + 5,
            i,
            f"{row.capital}",
            va="center",
            fontsize=9,
        )
    ax.set_xlabel("Best-capital disposable savings ($/week)")
    ax.set_title("Best capital city per occupation (alone, median rent, central living costs)")
    fig.tight_layout()
    fig.savefig(FIG / "savings_best_capital_by_occupation.png", dpi=150)
    plt.close(fig)

    # Summary JSON
    overall_best = central.loc[central["disposable_savings_weekly_aud"].idxmax()]
    overall_worst = central.loc[central["disposable_savings_weekly_aud"].idxmin()]
    summary = {
        "best_overall_weekly_aud": float(overall_best["disposable_savings_weekly_aud"]),
        "best_overall_occupation": overall_best["title"],
        "best_overall_capital": overall_best["capital"],
        "best_overall_anzsco": overall_best["anzsco"],
        "worst_overall_weekly_aud": float(overall_worst["disposable_savings_weekly_aud"]),
        "worst_overall_capital": overall_worst["capital"],
        "worst_overall_occupation": overall_worst["title"],
        "tax_year": INCOME_YEAR,
        "tax_source": ATO_TAX_RATES_URL,
        "earnings_state_scaling": "EEH May 2025 occupation national × state EEH relativity (estimate)",
    }
    pd.Series(summary).to_json(PROC / "savings_summary.json", indent=2)
    return summary
