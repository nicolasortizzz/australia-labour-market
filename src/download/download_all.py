#!/usr/bin/env python3
"""Download all official datasets and update data/manifest.json + data/SOURCES.md."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.download import config as cfg  # noqa: E402
from src.download.http_utils import download_file, wayback_url  # noqa: E402
from src.io.rba_fx import latest_aud_usd  # noqa: E402
from src.manifest import register_download, set_aud_usd_rate  # noqa: E402

RAW = ROOT / "data" / "raw"


def abs_url(release_slug: str, filename: str) -> str:
    # Caller passes path segment after /statistics/...
    raise NotImplementedError


def download_abs(relative_path: str, key: str, description: str, filename: str) -> None:
    url = f"{cfg.ABS_BASE}{relative_path}"
    dest = RAW / filename
    download_file(url, dest)
    register_download(key, description, url, dest)


def download_with_wayback_fallback(
    key: str,
    description: str,
    direct_url: str,
    filename: str,
    wayback_timestamp: str,
    wayback_note: str,
) -> None:
    dest = RAW / filename
    notes = ""
    try:
        download_file(direct_url, dest, timeout=60, retries=1)
    except Exception:
        wb = wayback_url(direct_url, wayback_timestamp)
        download_file(wb, dest, timeout=180, retries=2)
        notes = wayback_note
    register_download(key, description, direct_url, dest, notes=notes)


def download_wa_rental_bonds_zip() -> None:
    """Latest WA rental-bond zip from National Housing Data Exchange (official WA bonds)."""
    with urllib.request.urlopen(cfg.WA_RENTAL_BONDS_ZIP_API, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    url = payload["result"]["resources"][0]["url"]
    dest = RAW / "wa_rental_bonds.zip"
    download_file(url, dest, timeout=300, retries=2)
    register_download(
        "wa_rental_bonds",
        "WA Consumer Protection rental bonds — monthly lodgement microdata (AHDAP)",
        url,
        dest,
        notes=f"Package landing page: {cfg.WA_RENTAL_BONDS_PACKAGE_URL}",
    )


def download_sa_private_rent_postcodes() -> None:
    dest = RAW / "sa_private_rent_by_postcode_2026-06.csv"
    notes = ""
    try:
        download_file(cfg.SA_PRIVATE_RENT_REPORT_URL, RAW / "sa_private_rent_report_2026-06.xlsx", retries=1)
    except Exception:
        notes = (
            "Direct Data SA XLSX returned HTTP 403 from build environment; "
            "postcode strata CSV ingested from CC BY mirror of the same Private Rent Report release."
        )
    download_file(cfg.SA_PRIVATE_RENT_POSTCODE_MIRROR_URL, dest, timeout=120, retries=2)
    register_download(
        "sa_private_rent_postcodes",
        "SA Housing Trust Private Rent Report — metropolitan strata (CBS bonds)",
        cfg.SA_PRIVATE_RENT_REPORT_URL,
        dest,
        notes=notes,
    )


def download_with_jsa_fallback(
    key: str,
    description: str,
    direct_url: str,
    filename: str,
    wayback_note: str,
) -> None:
    dest = RAW / filename
    notes = ""
    try:
        download_file(direct_url, dest, timeout=30, retries=1)
    except Exception:
        wb = wayback_url(direct_url, cfg.JSA_WAYBACK_TIMESTAMP)
        download_file(wb, dest, timeout=180, retries=2)
        notes = wayback_note
    register_download(key, description, direct_url, dest, notes=notes)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    awe_base = (
        f"/statistics/labour/earnings-and-working-conditions/"
        f"average-weekly-earnings-australia/{cfg.AWE_RELEASE}/"
    )
    for state, fname in cfg.AWE_STATE_FILES.items():
        download_abs(
            awe_base + fname,
            f"awe_{state.lower()}",
            f"ABS AWE Nov 2025 — Table 11 state {state} (trend)",
            f"awe_{state.lower()}_{fname}",
        )

    eeh_path = (
        f"/statistics/labour/earnings-and-working-conditions/"
        f"employee-earnings-and-hours-australia/{cfg.EEH_RELEASE}/"
        f"{cfg.EEH_STATES_FILE}"
    )
    download_abs(
        eeh_path,
        "eeh_states",
        "ABS EEH May 2025 — data cube (includes Table 9 by state)",
        cfg.EEH_STATES_FILE,
    )
    eeh_occ_path = (
        f"/statistics/labour/earnings-and-working-conditions/"
        f"employee-earnings-and-hours-australia/{cfg.EEH_RELEASE}/"
        f"{cfg.EEH_OCCUPATION_FILE}"
    )
    download_abs(
        eeh_occ_path,
        "eeh_occupation_4digit",
        "ABS EEH May 2025 — occupation 4-digit weekly cash (DO011 Table 1)",
        cfg.EEH_OCCUPATION_FILE,
    )

    hes_path = (
        f"/statistics/economy/finance/household-expenditure-survey-australia-summary-results/"
        f"{cfg.HES_SUMMARY_RELEASE}/{cfg.HES_SUMMARY_FILE}"
    )
    download_abs(
        hes_path,
        "hes_summary_201516",
        "ABS HES 2015-16 — summary tables (living-cost anchor)",
        cfg.HES_SUMMARY_FILE,
    )

    ato_dest = RAW / "ato_tax_rates_australian_residents.html"
    download_file(cfg.ATO_TAX_RATES_URL, ato_dest, timeout=60, retries=2)
    register_download(
        "ato_tax_rates_2025_26",
        "ATO — Australian resident tax rates (2025-26 brackets; Medicare levy noted on page)",
        cfg.ATO_TAX_RATES_URL,
        ato_dest,
        notes="Brackets implemented in src/io/ato_tax.py for reproducible after-tax income.",
    )

    cpi_base = (
        f"/statistics/economy/price-indexes-and-inflation/"
        f"consumer-price-index-australia/{cfg.CPI_RELEASE}/"
    )
    download_abs(
        cpi_base + cfg.CPI_CAPITAL_GROUPS,
        "cpi_capital_groups",
        "ABS CPI Dec 2024 — Table 5 groups by capital city",
        cfg.CPI_CAPITAL_GROUPS,
    )
    download_abs(
        cpi_base + cfg.CPI_CAPITAL_EXP_CLASS,
        "cpi_capital_expclass",
        "ABS CPI Dec 2024 — Table 9 expenditure class by capital city",
        cfg.CPI_CAPITAL_EXP_CLASS,
    )

    slci_path = (
        f"/statistics/economy/price-indexes-and-inflation/"
        f"selected-living-cost-indexes-australia/{cfg.SLCI_RELEASE}/"
        f"{cfg.SLCI_ALL_GROUPS}"
    )
    download_abs(
        slci_path,
        "slci_all_groups",
        "ABS SLCI Jun 2026 — all groups index",
        cfg.SLCI_ALL_GROUPS,
    )

    jv_path = (
        f"/statistics/labour/jobs/job-vacancies-australia/"
        f"{cfg.JOB_VACANCIES_RELEASE}/{cfg.JOB_VACANCIES_STATES}"
    )
    download_abs(
        jv_path,
        "abs_job_vacancies_states",
        "ABS Job Vacancies Aug 2026 — state series (IVI fallback/supplement)",
        cfg.JOB_VACANCIES_STATES,
    )

    download_with_jsa_fallback(
        "jsa_osl_2025",
        "JSA Occupation Shortage List 2025 (6-digit ANZSCO 2022)",
        cfg.JSA_OSL_URL,
        "jsa_occupation_shortage_list_2025.xlsx",
        "Primary JSA host unreachable from build environment; file retrieved via "
        f"Internet Archive Wayback ({cfg.JSA_WAYBACK_TIMESTAMP}) pointing at the same official URL.",
    )
    download_with_jsa_fallback(
        "jsa_ivi_anzsco2_states",
        "JSA Internet Vacancy Index — ANZSCO2 occupations by state (Aug 2025)",
        cfg.JSA_IVI_URL,
        "jsa_ivi_anzsco2_states_territories_aug2025.xlsx",
        "Primary JSA host unreachable; Wayback mirror of official JSA file URL.",
    )

    for key, url, fname, desc in [
        (
            "homeaffairs_csol",
            cfg.CSOL_PDF_URL,
            "homeaffairs_core_skills_occupation_list.pdf",
            "Department of Home Affairs — Core Skills Occupation List (PDF)",
        ),
        (
            "legislation_lin_19051",
            cfg.LIN_19051_PDF_URL,
            "legislation_lin_19051_skilled_occupations.pdf",
            "Federal Register of Legislation LIN 19/051 — MLTSSL/STSOL/ROL",
        ),
    ]:
        dest = RAW / fname
        download_file(url, dest)
        register_download(key, desc, url, dest)

    dest = RAW / "nsw_rental_bond_lodgements_nov2025.xlsx"
    download_file(cfg.NSW_RENT_LODGEMENT_URL, dest)
    register_download(
        "nsw_rental_bond_lodgements",
        "NSW Fair Trading — rental bond lodgements Nov 2025",
        cfg.NSW_RENT_LODGEMENT_URL,
        dest,
    )

    download_with_wayback_fallback(
        "vic_rental_report_tables_sep2025",
        "VIC Homes Victoria Rental Report — tables Sep quarter 2025 (Melbourne median)",
        cfg.VIC_RENTAL_REPORT_TABLES_URL,
        "vic_rental_report_tables_sep2025.xlsx",
        cfg.VIC_RENTAL_REPORT_WAYBACK_TIMESTAMP,
        "Primary dffh.vic.gov.au host unreachable; file retrieved via Internet Archive Wayback "
        f"({cfg.VIC_RENTAL_REPORT_WAYBACK_TIMESTAMP}) pointing at the same official URL.",
    )

    dest = RAW / "qld_rta_median_rents.xlsx"
    download_file(cfg.QLD_RTA_MEDIAN_RENTS_URL, dest, timeout=300)
    register_download(
        "qld_rta_median_rents",
        "QLD RTA — quarterly median rents from bond lodgements",
        cfg.QLD_RTA_MEDIAN_RENTS_URL,
        dest,
    )

    download_wa_rental_bonds_zip()

    dest = RAW / "tas_rental_bond_november_2025.xlsx"
    download_file(cfg.TAS_RENTAL_BOND_NOV2025_URL, dest, timeout=120)
    register_download(
        "tas_rental_bond_november_2025",
        "Tasmania rental bond lodgements — November 2025 (open data)",
        cfg.TAS_RENTAL_BOND_NOV2025_URL,
        dest,
    )

    download_sa_private_rent_postcodes()

    rba_dest = RAW / "rba_f11_exchange_rates.csv"
    download_file(cfg.RBA_F11_EXCHANGE_RATES_URL, rba_dest, timeout=120, retries=2)
    rba_rec = register_download(
        "rba_f11_exchange_rates",
        "RBA Table F11 — indicative exchange rates (monthly; AUD/USD column)",
        cfg.RBA_F11_EXCHANGE_RATES_URL,
        rba_dest,
        notes=f"Landing page: {cfg.RBA_F11_LANDING_URL}",
    )
    fx = latest_aud_usd(rba_dest)
    set_aud_usd_rate(
        rate=fx["aud_usd"],
        rate_date=str(fx["rate_date"]),
        url=cfg.RBA_F11_EXCHANGE_RATES_URL,
        source_key="rba_f11_exchange_rates",
        local_path=rba_rec.local_path,
        sha256=rba_rec.sha256,
        access_date=rba_rec.access_date,
    )

    print("Downloads complete. See data/SOURCES.md")


if __name__ == "__main__":
    main()
