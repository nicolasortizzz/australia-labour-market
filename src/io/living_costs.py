"""
Non-rent living costs from official ABS sources (CPI-scaled).

Anchor: HES 2015-16 Table 1 (ABS 6530.0) — average weekly household spend on goods
and services ($1,425) minus current housing costs ($279) → $1,146/week (national, 2015-16).

Lone-person living alone: HES key facts lone-person households $712/week total goods &
services; housing share scaled from national average → non-housing ≈ $572/week (2015-16).

Updated to analysis year via CPI all-groups (Dec 2024 capital indexes vs 2015-16 anchor).
Sensitivity: ±15% on national anchor (documented in outputs).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.io.cpi import load_cpi_all_groups_by_capital

# HES 2015-16 publication Table 1 & key statistics (ABS cat. no. 6530.0)
HES_SOURCE_URL = (
    "https://www.abs.gov.au/statistics/economy/finance/"
    "household-expenditure-survey-australia-summary-results/latest-release"
)
HES_LONE_PERSON_NON_HOUSING_WEEKLY_2015_16 = 572.5  # derived; see module docstring
HES_ANCHOR_YEAR_LABEL = "2015-16"
# CPI all-groups Australia Dec 2015-16 ≈ 110.4 (ABS 6401.0); Dec 2024 from capital average
CPI_AUSTRALIA_DEC_2015_16 = 110.4

SENSITIVITY_LOW_MULT = 0.85
SENSITIVITY_HIGH_MULT = 1.15


def load_non_rent_living_costs_by_capital(raw_dir: Path) -> pd.DataFrame:
    cpi = load_cpi_all_groups_by_capital(raw_dir)
    national_cpi_dec_2024 = float(cpi["cpi_all_groups_index"].mean())
    inflate = national_cpi_dec_2024 / CPI_AUSTRALIA_DEC_2015_16
    national_central_2024 = HES_LONE_PERSON_NON_HOUSING_WEEKLY_2015_16 * inflate
    out = cpi[["capital", "cpi_all_groups_index"]].copy()
    scale = out["cpi_all_groups_index"] / national_cpi_dec_2024
    out["non_rent_living_weekly_low_aud"] = national_central_2024 * SENSITIVITY_LOW_MULT * scale
    out["non_rent_living_weekly_central_aud"] = national_central_2024 * scale
    out["non_rent_living_weekly_high_aud"] = national_central_2024 * SENSITIVITY_HIGH_MULT * scale
    out["non_rent_cost_source"] = (
        f"HES {HES_ANCHOR_YEAR_LABEL} lone-person non-housing weekly anchor, "
        f"CPI-scaled (ABS 6401.0 capital indexes Dec 2024)"
    )
    out["hes_source_url"] = HES_SOURCE_URL
    return out
