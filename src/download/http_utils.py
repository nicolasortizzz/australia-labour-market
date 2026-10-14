from __future__ import annotations

import time
from pathlib import Path

import requests

DEFAULT_HEADERS = {
    "User-Agent": "australia-labour-market-research/1.0 (reproducible analysis; contact: repo README)",
}


def download_file(
    url: str,
    dest: Path,
    timeout: int = 120,
    retries: int = 3,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=timeout,
                stream=True,
            ) as resp:
                resp.raise_for_status()
                with dest.open("wb") as f:
                    for chunk in resp.iter_content(chunk_size=1 << 20):
                        if chunk:
                            f.write(chunk)
            if dest.stat().st_size < 100:
                raise IOError(f"Download too small: {dest}")
            return
        except Exception as e:  # noqa: BLE001 — retry loop
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to download {url}: {last_err}")


def wayback_url(original_url: str, timestamp: str) -> str:
    return f"https://web.archive.org/web/{timestamp}/{original_url}"
