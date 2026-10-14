"""Australian resident income tax — ATO published rates (excludes Medicare levy in brackets)."""

from __future__ import annotations

# Source: ATO "Tax rates – Australian resident", resident rates 2025–26
# https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents
# Accessed via project download (see data/manifest.json key ato_tax_rates_2025_26).
ATO_TAX_RATES_URL = "https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents"
INCOME_YEAR = "2025-26"
MEDICARE_LEVY_RATE = 0.02

# (upper_bound_exclusive_or_inf, base_tax, marginal_rate) — brackets apply to taxable income
_RESIDENT_BRACKETS_2025_26: list[tuple[float, float, float]] = [
    (18_200, 0.0, 0.0),
    (45_000, 0.0, 0.16),
    (135_000, 4_288.0, 0.30),
    (190_000, 31_288.0, 0.37),
    (float("inf"), 51_638.0, 0.45),
]


def income_tax_resident_annual(taxable_income: float) -> float:
    """Tax on taxable income using ATO 2025–26 resident brackets (no offsets)."""
    if taxable_income <= 0:
        return 0.0
    tax = 0.0
    lower = 0.0
    for upper, base_at_lower, rate in _RESIDENT_BRACKETS_2025_26:
        if taxable_income <= upper:
            tax = base_at_lower + (taxable_income - lower) * rate
            break
        lower = upper
    return max(tax, 0.0)


def medicare_levy_annual(taxable_income: float) -> float:
    """Standard 2% Medicare levy on taxable income (no low-income exemptions modelled)."""
    if taxable_income <= 0:
        return 0.0
    return taxable_income * MEDICARE_LEVY_RATE


def after_tax_weekly_cash(gross_annual: float, weeks_per_year: float = 52.0) -> dict[str, float]:
    """Gross cash earnings → after tax and Medicare (super excluded)."""
    taxable = gross_annual
    tax = income_tax_resident_annual(taxable)
    medicare = medicare_levy_annual(taxable)
    net_annual = gross_annual - tax - medicare
    return {
        "gross_annual_aud": gross_annual,
        "income_tax_annual_aud": tax,
        "medicare_levy_annual_aud": medicare,
        "net_annual_aud": net_annual,
        "net_weekly_aud": net_annual / weeks_per_year,
        "effective_tax_rate_pct": 100.0 * (tax + medicare) / gross_annual if gross_annual else 0.0,
    }
