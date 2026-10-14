"""Official source URLs and release paths (update when new ABS/JSA releases ship)."""

from __future__ import annotations

ABS_BASE = "https://www.abs.gov.au"

# Average Weekly Earnings — November 2025 (6302.0)
AWE_RELEASE = "nov-2025"
AWE_STATE_FILES = {
    "NSW": "63020011A.xlsx",
    "VIC": "63020011B.xlsx",
    "QLD": "63020011C.xlsx",
    "SA": "63020011D.xlsx",
    "WA": "63020011E.xlsx",
    "TAS": "63020011F.xlsx",
    "NT": "63020011G.xlsx",
    "ACT": "63020011H.xlsx",
}

# Employee Earnings and Hours — May 2025 (6306.0)
EEH_RELEASE = "may-2025"
EEH_STATES_FILE = "63060DO001_202505.xlsx"

# CPI — December quarter 2024 (6401.0)
CPI_RELEASE = "dec-quarter-2024"
CPI_CAPITAL_GROUPS = "640103.xlsx"  # Table 5 — groups by capital city
CPI_CAPITAL_EXP_CLASS = "640107.xlsx"  # Table 9 — expenditure class by capital city

# Selected Living Cost Indexes — June 2026 (6467.0)
SLCI_RELEASE = "jun-2026"
SLCI_ALL_GROUPS = "646701.xlsx"

# Jobs and Skills Australia (direct; may be unreachable — Wayback fallback in downloader)
JSA_OSL_URL = (
    "https://www.jobsandskills.gov.au/sites/default/files/2025-10/"
    "2025%20Occupation%20Shortage%20List%20-%206%20digit%20ANZSCO%20and%20OSCA.xlsx"
)
JSA_IVI_URL = (
    "https://www.jobsandskills.gov.au/sites/default/files/2025-09/"
    "internet_vacancies_anzsco2_occupations_states_and_territories_-_august_2025.xlsx"
)
JSA_WAYBACK_TIMESTAMP = "20251001000000"

# Home Affairs / legislation
CSOL_PDF_URL = "https://immi.homeaffairs.gov.au/Documents/core-sol.pdf"
LIN_19051_PDF_URL = (
    "https://www.legislation.gov.au/F2019L00278/2024-12-14/2024-12-14/text/original/pdf"
)

# NSW Fair Trading rental bond lodgements (official NSW Government)
NSW_RENT_LODGEMENT_URL = (
    "https://www.nsw.gov.au/sites/default/files/noindex/2025-12/"
    "rentalbond_lodgements_november_2025.xlsx"
)

# ABS Job Vacancies — official fallback if IVI download fails (6354.0)
JOB_VACANCIES_RELEASE = "aug-2026"
JOB_VACANCIES_STATES = "6354002.xlsx"

STATE_TO_CAPITAL = {
    "NSW": "Sydney",
    "VIC": "Melbourne",
    "QLD": "Brisbane",
    "SA": "Adelaide",
    "WA": "Perth",
    "TAS": "Hobart",
    "NT": "Darwin",
    "ACT": "Canberra",
}
