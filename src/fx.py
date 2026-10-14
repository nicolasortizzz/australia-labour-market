"""
AUD ↔ USD helpers for all monetary outputs.

Future tables, charts, and README figures that show money must use these functions
so conversions stay aligned with `data/manifest.json` → `aud_usd` (RBA F11).

Do not hard-code exchange rates in analysis or documentation.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.manifest import load_manifest


def aud_usd_rate() -> float:
    """USD per 1 AUD from manifest (populated when RBA F11 is downloaded)."""
    manifest = load_manifest()
    block = manifest.get("aud_usd")
    if not block or "rate" not in block:
        raise RuntimeError(
            "manifest.json has no aud_usd block; run `make data` to fetch RBA F11"
        )
    return float(block["rate"])


def aud_usd_metadata() -> dict:
    manifest = load_manifest()
    block = manifest.get("aud_usd")
    if not block:
        raise RuntimeError("manifest.json has no aud_usd block")
    return dict(block)


def aud_to_usd(amount_aud: float, rate: float | None = None) -> float:
    r = rate if rate is not None else aud_usd_rate()
    return float(amount_aud) * r


def format_aud(amount_aud: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"A${amount_aud:,.0f}"
    return f"A${amount_aud:,.{decimals}f}"


def format_usd(amount_usd: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"US${amount_usd:,.0f}"
    return f"US${amount_usd:,.{decimals}f}"


def format_aud_usd_pair(amount_aud: float, rate: float | None = None, decimals: int = 0) -> str:
    """Label form: A$X (US$Y)."""
    usd = aud_to_usd(amount_aud, rate=rate)
    return f"{format_aud(amount_aud, decimals)} ({format_usd(usd, decimals)})"


def add_usd_columns(
    df: pd.DataFrame,
    aud_columns: Iterable[str],
    rate: float | None = None,
    suffix_aud: str = "_aud",
    suffix_usd: str = "_usd",
) -> pd.DataFrame:
    """Add parallel USD columns for each listed AUD column (copies frame)."""
    out = df.copy()
    r = rate if rate is not None else aud_usd_rate()
    for col in aud_columns:
        if col not in out.columns:
            raise KeyError(col)
        base = col.removesuffix(suffix_aud) if col.endswith(suffix_aud) else col
        usd_col = f"{base}{suffix_usd}" if base != col else f"{col}{suffix_usd}"
        out[usd_col] = out[col].astype(float) * r
    return out


def matplotlib_aud_usd_formatter(rate: float | None = None, decimals: int = 0):
    """Return a matplotlib axis formatter for AUD values with USD in parentheses."""
    r = rate if rate is not None else aud_usd_rate()

    def _fmt(x: float, _pos: int) -> str:
        if decimals == 0:
            return f"A${x:,.0f}\n(US${x * r:,.0f})"
        return f"A${x:,.{decimals}f}\n(US${x * r:,.{decimals}f})"

    return _fmt
