"""Combine observed capital medians with CPI-scaled imputation fallback."""

from __future__ import annotations

import pandas as pd

IMPUTATION_LABEL = "NSW bond median × (city CPI rent / Sydney CPI rent) [fallback]"


def impute_from_nsw_anchor(cpi_rents: pd.DataFrame, nsw_median: float) -> pd.DataFrame:
    sydney_idx = float(
        cpi_rents.loc[cpi_rents["capital"] == "Sydney", "cpi_rent_index"].iloc[0]
    )
    out = cpi_rents[["capital"]].copy()
    out["median_weekly_rent_aud"] = nsw_median * (cpi_rents["cpi_rent_index"] / sydney_idx)
    out["rent_observed"] = False
    out["rent_source"] = "ABS CPI rent/housing index scaling"
    out["rent_method"] = IMPUTATION_LABEL
    out["period_label"] = "Scaled to NSW bond anchor period"
    out["n_observations"] = None
    return out


def merge_observed_and_imputed(
    cpi_rents: pd.DataFrame,
    observed: pd.DataFrame,
    nsw_median: float,
) -> pd.DataFrame:
    imputed = impute_from_nsw_anchor(cpi_rents, nsw_median)
    obs = observed.set_index("capital")
    merged = imputed.set_index("capital")
    for col in [
        "median_weekly_rent_aud",
        "rent_observed",
        "rent_source",
        "rent_method",
        "period_label",
        "n_observations",
    ]:
        merged.loc[obs.index, col] = obs[col]
    merged = merged.reset_index()
    merged["rent_imputation"] = merged["rent_method"]
    return merged
