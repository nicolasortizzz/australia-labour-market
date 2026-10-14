"""Capital-city rent scenarios: all-dwellings median, 1-bed where published, share-house assumption."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.io.rents_merge import merge_observed_and_imputed
from src.io.rents_nsw import load_nsw_weekly_rents
from src.io.rents_observed import (
    SA_METRO_POSTCODE_MAX,
    SA_METRO_POSTCODE_MIN,
    TAS_HOBART_POSTCODES,
    WA_METRO_POSTCODE_MAX,
    WA_METRO_POSTCODE_MIN,
    load_all_observed_medians,
)
from src.io.cpi import load_cpi_rents_by_capital


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = w.cumsum()
    idx = int(np.searchsorted(cum, w.sum() / 2.0))
    return float(v[min(idx, len(v) - 1)])


def _nsw_sydney_bedroom_medians(path: Path) -> dict[str, float]:
    """NSW bond microdata — Sydney region postcodes 2000–2234."""
    xl = pd.ExcelFile(path)
    sheet = xl.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet, header=2)
    df = df.rename(columns=lambda c: str(c).strip())
    pc = pd.to_numeric(df["Postcode"], errors="coerce")
    mask = (pc >= 2000) & (pc <= 2234)
    sub = df.loc[mask].copy()
    sub["Weekly Rent"] = pd.to_numeric(sub["Weekly Rent"], errors="coerce")
    sub["Bedrooms"] = pd.to_numeric(sub["Bedrooms"], errors="coerce")
    sub = sub[(sub["Weekly Rent"] >= 50) & (sub["Weekly Rent"] <= 5000)]
    out: dict[str, float] = {}
    for bed, key in [(1, "one_bed"), (2, "two_bed")]:
        b = sub[sub["Bedrooms"] == bed]
        if len(b) >= 30:
            out[key] = float(b["Weekly Rent"].median())
    return out


def _wa_metro_bedroom_medians(zip_path: Path) -> dict[str, float]:
    with zipfile.ZipFile(zip_path) as zf:
        csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        df = pd.read_csv(io.BytesIO(zf.read(csv_name)))
    pc = pd.to_numeric(df.get("postcode", df.get("Postcode")), errors="coerce")
    rent = pd.to_numeric(df.get("weekly_rent", df.get("Weekly Rent")), errors="coerce")
    beds = pd.to_numeric(df.get("bedrooms", df.get("Bedrooms")), errors="coerce")
    mask = (pc >= WA_METRO_POSTCODE_MIN) & (pc <= WA_METRO_POSTCODE_MAX)
    sub = pd.DataFrame({"rent": rent, "beds": beds}).loc[mask].dropna()
    sub = sub[(sub["rent"] >= 50) & (sub["rent"] <= 5000)]
    out: dict[str, float] = {}
    for bed, key in [(1, "one_bed"), (2, "two_bed")]:
        b = sub[sub["beds"] == bed]
        if len(b) >= 30:
            out[key] = float(b["rent"].median())
    return out


def _sa_metro_bedroom_medians(csv_path: Path) -> dict[str, float]:
    df = pd.read_csv(csv_path)
    df["postcode"] = pd.to_numeric(df["postcode"], errors="coerce")
    metro = df[(df["postcode"] >= SA_METRO_POSTCODE_MIN) & (df["postcode"] <= SA_METRO_POSTCODE_MAX)]
    metro = metro[metro["suppressed"].isna() | (metro["suppressed"] == "")]
    metro["median_weekly_rent"] = pd.to_numeric(metro["median_weekly_rent"], errors="coerce")
    metro["bonds_lodged"] = pd.to_numeric(metro["bonds_lodged"], errors="coerce").fillna(1)
    out: dict[str, float] = {}
    for bed_label, key in [("1 bedroom", "one_bed"), ("2 bedrooms", "two_bed")]:
        b = metro[metro["bedrooms"] == bed_label].dropna(subset=["median_weekly_rent"])
        if len(b) >= 5:
            out[key] = _weighted_median(
                b["median_weekly_rent"].values, b["bonds_lodged"].values
            )
    return out


def _vic_melbourne_bedroom_medians(xlsx_path: Path) -> dict[str, float]:
    df = pd.read_excel(xlsx_path, sheet_name="Table 3", header=None)
    out: dict[str, float] = {}
    for i in range(len(df)):
        label = str(df.iloc[i, 0]).strip()
        if label == "1 Bed Flat":
            out["one_bed"] = float(df.iloc[i, 1])
        if label == "2 Bed Flat":
            out["two_bed"] = float(df.iloc[i, 1])
    return out


def _qld_brisbane_bedroom_medians(xlsx_path: Path) -> dict[str, float]:
    """QLD RTA workbook — Brisbane (C) dwelling-type medians, latest Sep 2025 quarter."""
    df = pd.read_excel(xlsx_path, sheet_name="7 lga-rents ", header=None)
    years = df.iloc[6, 4:].tolist()
    quarters = df.iloc[5, 4:].tolist()
    col_idx = None
    for i, (q, y) in enumerate(zip(quarters, years)):
        if q == "Sep" and y == 2025:
            col_idx = 4 + i
            break
    if col_idx is None:
        return {}
    out: dict[str, float] = {}
    mapping = {
        "Flat 1": "one_bed",
        "Flat 2": "two_bed",
        "Flat/unit 1 bedroom": "one_bed",
        "Flat/unit 2 bedrooms": "two_bed",
    }
    for dwell, key in mapping.items():
        row = df[(df[2] == "Brisbane (C)") & (df[3] == dwell)]
        if not row.empty:
            val = pd.to_numeric(row.iloc[0, col_idx], errors="coerce")
            if pd.notna(val):
                out[key] = float(val)
    return out


def build_rent_scenarios(raw_dir: Path) -> pd.DataFrame:
    """Weekly rent ($) by capital and housing scenario."""
    cpi_rent = load_cpi_rents_by_capital(raw_dir)
    nsw_median = float(
        load_nsw_weekly_rents(raw_dir / "nsw_rental_bond_lodgements_nov2025.xlsx")
        .loc[lambda d: d["metric"] == "median_weekly_rent_aud", "value"]
        .iloc[0]
    )
    observed = load_all_observed_medians(raw_dir)
    base_rents = merge_observed_and_imputed(cpi_rent, observed, nsw_median)

    bedroom: dict[str, dict[str, float]] = {}
    try:
        bedroom["Sydney"] = _nsw_sydney_bedroom_medians(
            raw_dir / "nsw_rental_bond_lodgements_nov2025.xlsx"
        )
    except Exception:
        bedroom["Sydney"] = {}
    try:
        bedroom["Melbourne"] = _vic_melbourne_bedroom_medians(
            raw_dir / "vic_rental_report_tables_sep2025.xlsx"
        )
    except Exception:
        bedroom["Melbourne"] = {}
    try:
        bedroom["Brisbane"] = _qld_brisbane_bedroom_medians(raw_dir / "qld_rta_median_rents.xlsx")
    except Exception:
        bedroom["Brisbane"] = {}
    try:
        bedroom["Perth"] = _wa_metro_bedroom_medians(raw_dir / "wa_rental_bonds.zip")
    except Exception:
        bedroom["Perth"] = {}
    try:
        bedroom["Adelaide"] = _sa_metro_bedroom_medians(
            raw_dir / "sa_private_rent_by_postcode_2026-06.csv"
        )
    except Exception:
        bedroom["Adelaide"] = {}

    rows: list[dict] = []
    for _, r in base_rents.iterrows():
        cap = r["capital"]
        all_med = float(r["median_weekly_rent_aud"])
        beds = bedroom.get(cap, {})
        one = beds.get("one_bed")
        two = beds.get("two_bed")
        one_observed = beds.get("one_bed") is not None
        two_observed = beds.get("two_bed") is not None
        one = beds.get("one_bed") if one_observed else all_med * 0.85
        two = beds.get("two_bed") if two_observed else all_med * 1.05
        share_rent = 0.5 * two
        for scenario, rent, note in [
            ("alone_all_median", all_med, r.get("rent_method", "")),
            (
                "alone_1bed",
                one,
                "observed_1bed_median" if one_observed else "estimate_ratio_0.85_all_median",
            ),
            (
                "share_flat_half_2bed",
                share_rent,
                "assumption_50pct_of_2bed_median"
                if two_observed
                else "assumption_50pct_of_estimated_2bed",
            ),
        ]:
            rows.append(
                {
                    "capital": cap,
                    "rent_scenario": scenario,
                    "weekly_rent_aud": rent,
                    "rent_observed_base": bool(r["rent_observed"]),
                    "rent_scenario_note": note,
                    "rent_period": r.get("period_label"),
                }
            )
    return pd.DataFrame(rows)
