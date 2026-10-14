"""Record download provenance: URL, access date, SHA-256."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "manifest.json"
SOURCES_MD_PATH = ROOT / "data" / "SOURCES.md"


@dataclass
class SourceRecord:
    key: str
    description: str
    url: str
    local_path: str
    access_date: str
    sha256: str
    bytes: int
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"generated": today_iso(), "sources": []}


def save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest["generated"] = today_iso()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_sources_md(manifest)


def register_download(
    key: str,
    description: str,
    url: str,
    local_path: Path,
    notes: str = "",
) -> SourceRecord:
    if not local_path.is_file():
        raise FileNotFoundError(local_path)
    rec = SourceRecord(
        key=key,
        description=description,
        url=url,
        local_path=str(local_path.relative_to(ROOT)),
        access_date=today_iso(),
        sha256=sha256_file(local_path),
        bytes=local_path.stat().st_size,
        notes=notes,
    )
    manifest = load_manifest()
    sources = [s for s in manifest.get("sources", []) if s.get("key") != key]
    sources.append(rec.to_dict())
    manifest["sources"] = sorted(sources, key=lambda s: s["key"])
    save_manifest(manifest)
    return rec


def write_sources_md(manifest: dict[str, Any]) -> None:
    lines = [
        "# Data sources manifest",
        "",
        f"Auto-generated on **{manifest.get('generated', today_iso())}** from `data/manifest.json`.",
        "",
        "| Key | Description | URL | Local file | Access date | SHA-256 | Size (bytes) | Notes |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for s in manifest.get("sources", []):
        url = s["url"].replace("|", "%7C")
        notes = (s.get("notes") or "").replace("|", "/")
        lines.append(
            f"| {s['key']} | {s['description']} | {url} | `{s['local_path']}` | "
            f"{s['access_date']} | `{s['sha256'][:16]}…` | {s['bytes']} | {notes} |"
        )
    lines.extend(
        [
            "",
            "## Unavailable or blocked at download time",
            "",
            "See notes in the table above and `README.md` limitations section.",
            "",
        ]
    )
    SOURCES_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
