"""Official median weekly rent series by capital city (bond / rental-report sources)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.io.rents_nsw import load_nsw_weekly_rents

# Greater Perth: common metropolitan postcodes (Consumer Protection bond lodgements).
WA_METRO_POSTCODE_MIN = 6000
WA_METRO_POSTCODE_MAX = 6199

# Greater Hobart Statistical Area (approximate postcodes for bond microdata).
TAS_HOBART_POSTCODES = frozenset(
    set(range(7000, 7025))
    | {7050, 7052, 7053, 7054, 7055, 7170, 7171, 7172}
)

# Metropolitan Adelaide (Private Rent Report; postcode-level strata).
SA_METRO_POSTCODE_MIN = 5000
SA_METRO_POSTCODE_MAX = 5199


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = w.cumsum()
    idx = int(np.searchsorted(cum, w.sum() / 2.0))
    return float(v[min(idx, len(v) - 1)])


def _clean_weekly_rents(series: pd.Series) -> pd.Series:
    rent = pd.to_numeric(series, errors="coerce")
    return rent[(rent >= 50) & (rent <= 5000)]


def load_vic_melbourne_median(path: Path) -> dict:
    """Homes Victoria Rental Report tables — metropolitan Melbourne, all property types."""
    df = pd.read_excel(path, sheet_name="Table 1", header=None)
    row = df[df.iloc[:, 0].astype(str).str.strip().str.lower() == "melbourne"]
    if row.empty:
        raise ValueError("Melbourne row not found in VIC Rental Report Table 1")
    # Columns: label, empty, index, qtr change, ann change — median is first numeric after name
    vals = pd.to_numeric(row.iloc[0, 1:], errors="coerce").dropna()
    median = float(vals.iloc[0])
    return {
        "capital": "Melbourne",
        "median_weekly_rent_aud": median,
        "period_label": "Sep quarter 2025",
        "rent_observed": True,
        "rent_source": "VIC Homes Victoria Rental Report (RTBA bond lodgements)",
        "rent_method": "Published metropolitan Melbourne median (Table 1, all properties)",
        "n_observations": None,
    }


def load_qld_brisbane_median(path: Path, quarter_year: int = 2025, quarter_month: str = "Sep") -> dict:
    df = pd.read_excel(path, sheet_name="7 lga-rents ", header=None)
    row = df[(df[2] == "Brisbane (C)") & (df[3] == "All dwellings")].iloc[0]
    years = df.iloc[6, 4:].tolist()
    quarters = df.iloc[5, 4:].tolist()
    col_idx = None
    for i, (q, y) in enumerate(zip(quarters, years)):
        if q == quarter_month and y == quarter_year:
            col_idx = 4 + i
            break
    if col_idx is None:
        raise ValueError(f"Quarter {quarter_month} {quarter_year} not found in QLD RTA workbook")
    median = float(row[col_idx])
    return {
        "capital": "Brisbane",
        "median_weekly_rent_aud": median,
        "period_label": f"{quarter_month} quarter {quarter_year}",
        "rent_observed": True,
        "rent_source": "QLD Residential Tenancies Authority median rents (bond lodgements)",
        "rent_method": "Brisbane (C) LGA, all dwellings, published quarterly median",
        "n_observations": None,
    }


def load_wa_perth_median_from_zip(path: Path, year: int = 2025, month: int = 11) -> dict:
    """Median weekly rent from Nov 2025 Perth metro bond lodgements (Consumer Protection)."""
    range_tag = f"01-{month:02d}-{year}"  # e.g. (01-11-2025-30-11-2025) in WA CSV archive names
    with zipfile.ZipFile(path) as zf:
        candidates = [
            n
            for n in zf.namelist()
            if "Monthly Bond Lodgement Summary" in n
            and range_tag in n
            and "__MACOSX" not in n
        ]
        if not candidates:
            raise ValueError(f"No WA lodgement file for {year}-{month:02d} in {path.name}")
        raw = zf.read(candidates[0])
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip().upper() for c in df.columns]
    rent = _clean_weekly_rents(df["WEEKLY RENT AMOUNT"])
    pc = pd.to_numeric(df["POSTCODE"], errors="coerce")
    metro = (pc >= WA_METRO_POSTCODE_MIN) & (pc <= WA_METRO_POSTCODE_MAX)
    clean = rent[metro.reindex(rent.index, fill_value=False)]
    return {
        "capital": "Perth",
        "median_weekly_rent_aud": float(clean.median()),
        "period_label": f"{year}-{month:02d} (monthly lodgements)",
        "rent_observed": True,
        "rent_source": "WA Consumer Protection rental bond lodgements (DMIRS/AHDAP release)",
        "rent_method": f"Median weekly rent, Greater Perth postcodes {WA_METRO_POSTCODE_MIN}–{WA_METRO_POSTCODE_MAX}",
        "n_observations": int(clean.notna().sum()),
    }


def load_tas_hobart_median(path: Path) -> dict:
    raw = pd.read_excel(path, sheet_name="Active Bonds", header=None)
    header_row = 0
    for i in range(min(5, len(raw))):
        if str(raw.iloc[i, 0]).strip().lower() == "suburb":
            header_row = i
            break
    header = [str(x).strip() for x in raw.iloc[header_row]]
    df = raw.iloc[header_row + 1 :].copy()
    df.columns = header
    rent_col = next(c for c in df.columns if "weekly" in c.lower() and "rent" in c.lower())
    pc_col = next(c for c in df.columns if "postcode" in c.lower())
    rent = _clean_weekly_rents(df[rent_col])
    pc = pd.to_numeric(df[pc_col], errors="coerce")
    metro = pc.isin(TAS_HOBART_POSTCODES)
    clean = rent[metro.reindex(rent.index, fill_value=False)]
    return {
        "capital": "Hobart",
        "median_weekly_rent_aud": float(clean.median()),
        "period_label": "Nov 2025 (monthly bond lodgements)",
        "rent_observed": True,
        "rent_source": "Tasmania Department of Justice rental bond open data",
        "rent_method": "Median weekly rent, Greater Hobart postcodes (bond lodgements)",
        "n_observations": int(clean.notna().sum()),
    }


def load_sa_adelaide_metro_median_postcode_csv(path: Path) -> dict:
    """Metropolitan Adelaide from SA Private Rent Report postcode strata (CBS bonds)."""
    df = pd.read_csv(path)
    pc = df["postcode"].astype(str).str.zfill(4)
    metro = pc.str.match(r"^(50|51[0-9]{2})$", na=False)
    sub = df.loc[metro].copy()
    sub = sub[pd.to_numeric(sub["bonds_lodged"], errors="coerce") > 0]
    sub = sub[pd.to_numeric(sub["median_weekly_rent"], errors="coerce") > 0]
    vals = sub["median_weekly_rent"].astype(float).values
    weights = sub["bonds_lodged"].astype(float).values
    median = _weighted_median(vals, weights)
    return {
        "capital": "Adelaide",
        "median_weekly_rent_aud": float(median),
        "period_label": "Apr–Jun 2026 (quarterly report)",
        "rent_observed": True,
        "rent_source": "SA Housing Trust Private Rent Report (CBS rental bonds)",
        "rent_method": "Bond-weighted median across metropolitan Adelaide postcode/dwelling strata",
        "n_observations": int(weights.sum()),
    }


def load_nsw_sydney_median(path: Path) -> dict:
    stats = load_nsw_weekly_rents(path)
    median = float(stats.loc[stats["metric"] == "median_weekly_rent_aud", "value"].iloc[0])
    n = int(stats.loc[stats["metric"] == "n_lodgements", "value"].iloc[0])
    return {
        "capital": "Sydney",
        "median_weekly_rent_aud": median,
        "period_label": "Nov 2025 (monthly bond lodgements)",
        "rent_observed": True,
        "rent_source": "NSW Fair Trading rental bond lodgements",
        "rent_method": "Median weekly rent, all NSW lodgements (state proxy for Sydney capital)",
        "n_observations": n,
    }


def load_all_observed_medians(raw_dir: Path) -> pd.DataFrame:
    rows = [
        load_nsw_sydney_median(raw_dir / "nsw_rental_bond_lodgements_nov2025.xlsx"),
        load_vic_melbourne_median(raw_dir / "vic_rental_report_tables_sep2025.xlsx"),
        load_qld_brisbane_median(raw_dir / "qld_rta_median_rents.xlsx"),
        load_wa_perth_median_from_zip(raw_dir / "wa_rental_bonds.zip"),
        load_sa_adelaide_metro_median_postcode_csv(raw_dir / "sa_private_rent_by_postcode_2026-06.csv"),
        load_tas_hobart_median(raw_dir / "tas_rental_bond_november_2025.xlsx"),
    ]
    return pd.DataFrame(rows)
