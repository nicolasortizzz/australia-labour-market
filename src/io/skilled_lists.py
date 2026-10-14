from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pdfplumber


def _parse_csol_table(path: Path) -> set[str]:
    codes: set[str] = set()
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    for cell in row:
                        if cell and re.fullmatch(r"\d{6}", str(cell).strip()):
                            codes.add(str(cell).strip())
    return codes


def load_csol_codes(path: Path) -> pd.DataFrame:
    codes = sorted(_parse_csol_table(path))
    return pd.DataFrame({"anzsco": codes, "on_csol": True})


def load_lin_19051_lists(path: Path) -> dict[str, set[str]]:
    """Extract ANZSCO codes mentioned under MLTSSL / STSOL / ROL headings (6-digit)."""
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    text = "\n".join(text_parts)
    lists = {"MLTSSL": set(), "STSOL": set(), "ROL": set()}
    section = None
    for line in text.splitlines():
        upper = line.upper()
        if "MEDIUM AND LONG-TERM STRATEGIC SKILLS LIST" in upper or upper.strip() == "MLTSSL":
            section = "MLTSSL"
            continue
        if "SHORT-TERM SKILLED OCCUPATION LIST" in upper or upper.strip() == "STSOL":
            section = "STSOL"
            continue
        if "REGIONAL OCCUPATION LIST" in upper or upper.strip() == "ROL":
            section = "ROL"
            continue
        if section:
            for code in re.findall(r"\b(\d{6})\b", line):
                lists[section].add(code)
    return lists

