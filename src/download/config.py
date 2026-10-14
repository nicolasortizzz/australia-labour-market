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
EEH_OCCUPATION_FILE = "63060DO011_202505.xlsx"

# HES 2015-16 summary (non-rent living-cost anchor)
HES_SUMMARY_FILE = "65300DO011_201516.xlsx"
HES_SUMMARY_RELEASE = "2015-16"

# ATO resident tax rates (HTML reference; brackets coded in src/io/ato_tax.py)
ATO_TAX_RATES_URL = "https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents"

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

# VIC Homes Victoria / DFFH Rental Report — Sep quarter 2025 tables (Melbourne median)
VIC_RENTAL_REPORT_TABLES_URL = (
    "https://www.dffh.vic.gov.au/tables-rental-report-september-quarter-2025-excel"
)
VIC_RENTAL_REPORT_WAYBACK_TIMESTAMP = "20260225000000"

# QLD RTA quarterly median rents workbook (all quarters in one file)
QLD_RTA_MEDIAN_RENTS_URL = (
    "https://www.rta.qld.gov.au/sites/default/files/2023-04/rta-bond-statistics.xlsx"
)

# WA Consumer Protection rental bonds — monthly lodgement microdata (AHDAP mirror)
WA_RENTAL_BONDS_PACKAGE_URL = (
    "https://housing-data-exchange.ahdap.org/dataset/west-australia-rental-bonds-data-2023-current"
)
WA_RENTAL_BONDS_ZIP_API = (
    "https://housing-data-exchange.ahdap.org/api/3/action/package_show"
    "?id=west-australia-rental-bonds-data-2023-current"
)

# TAS rental bond open data — November 2025
TAS_RENTAL_BOND_NOV2025_URL = (
    "https://data.gov.au/data/dataset/a5096409-4702-468e-94a7-303951b4173b/"
    "resource/df29642c-5d80-47f1-9f93-d4ca802ab6c3/download/abs-report-november-2025.xlsx"
)

# SA Private Rent Report — official Data SA (postcode strata CSV mirror when direct XLSX blocked)
SA_PRIVATE_RENT_REPORT_URL = (
    "https://data.sa.gov.au/data/dataset/8eb97a72-9919-448b-8de6-fc1530b3f7ec/"
    "resource/b4aa86f1-7efa-4690-9793-bd36df97ad29/download/private-rental-report-2026-06.xlsx"
)
SA_PRIVATE_RENT_POSTCODE_MIRROR_URL = (
    "https://publicdata.au/d/sa-private-rents-by-postcode/v/2026-08-11/data.csv"
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
