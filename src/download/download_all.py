#!/usr/bin/env python3
"""Download all official datasets and update data/manifest.json + data/SOURCES.md."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.download import config as cfg  # noqa: E402
from src.download.http_utils import download_file, wayback_url  # noqa: E402
from src.manifest import register_download  # noqa: E402

RAW = ROOT / "data" / "raw"


def abs_url(release_slug: str, filename: str) -> str:
    # Caller passes path segment after /statistics/...
    raise NotImplementedError


def download_abs(relative_path: str, key: str, description: str, filename: str) -> None:
    url = f"{cfg.ABS_BASE}{relative_path}"
    dest = RAW / filename
    download_file(url, dest)
    register_download(key, description, url, dest)


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

    print("Downloads complete. See data/SOURCES.md")


if __name__ == "__main__":
    main()
