"""Target occupations for 'where can you save the most?' analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfessionalProfile:
    anzsco: str
    title: str
    eeh_anzsco_4digit: str
    eeh_occupation_label: str
    earnings_note: str
    ivi_anzsco2: str
    ivi_group_title: str


# IVI sub-major groups (JSA IVI Trend sheet, Level 3, AUST)
PROFESSIONAL_PROFILES: tuple[ProfessionalProfile, ...] = (
    ProfessionalProfile(
        "224111",
        "Actuary",
        "2241",
        "Mathematical science professionals",
        "EEH May 2025 4-digit unit group (includes actuaries; 6-digit not published)",
        "2F",
        "Science Professionals and Veterinarians",
    ),
    ProfessionalProfile(
        "224311",
        "Economist",
        "2243",
        "Economists",
        "EEH May 2025 4-digit unit group",
        "2B",
        "Information Professionals",
    ),
    ProfessionalProfile(
        "222311",
        "Financial Investment Adviser",
        "2223",
        "Financial investment advisers and managers",
        "EEH May 2025 4-digit unit group (shared with 222312)",
        "2A",
        "Business, Finance and Human Resource Professionals",
    ),
    ProfessionalProfile(
        "222312",
        "Financial Investment Manager",
        "2223",
        "Financial investment advisers and managers",
        "EEH May 2025 4-digit unit group (same national average as 222311)",
        "2A",
        "Business, Finance and Human Resource Professionals",
    ),
    ProfessionalProfile(
        "2222",
        "Financial dealer (proxy for financial analyst roles)",
        "2222",
        "Financial dealers",
        "No separate 6-digit 'Financial Analyst' in EEH; 2222 is nearest published dealer group",
        "2A",
        "Business, Finance and Human Resource Professionals",
    ),
    ProfessionalProfile(
        "221111",
        "Accountant (General)",
        "2211",
        "Accountants",
        "EEH May 2025 4-digit unit group",
        "2A",
        "Business, Finance and Human Resource Professionals",
    ),
    ProfessionalProfile(
        "221112",
        "Management Accountant",
        "2211",
        "Accountants",
        "EEH May 2025 4-digit unit group (same national average as 221111)",
        "2A",
        "Business, Finance and Human Resource Professionals",
    ),
    ProfessionalProfile(
        "221113",
        "Taxation Accountant",
        "2211",
        "Accountants",
        "EEH May 2025 4-digit unit group",
        "2A",
        "Business, Finance and Human Resource Professionals",
    ),
    ProfessionalProfile(
        "224114",
        "Data Analyst",
        "2249",
        "Other information and organisation professionals",
        "ANZSCO 2022 224114 not in EEH tables; nearest 4-digit group 2249",
        "2B",
        "Information Professionals",
    ),
    ProfessionalProfile(
        "224115",
        "Data Scientist",
        "2241",
        "Mathematical science professionals",
        "EEH May 2025 4-digit unit group (shared with actuaries at 4-digit level)",
        "2B",
        "Information Professionals",
    ),
)
