from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import html
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(value: Any) -> str:
    """Turn Crossref's occasionally JATS-marked fields into plain text."""
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def _crossref_date(item: dict[str, Any]) -> str:
    for field in ("published", "published-print", "published-online", "issued"):
        parts = item.get(field, {}).get("date-parts", [[]])
        if parts and parts[0]:
            year, *rest = parts[0]
            month = rest[0] if rest else 1
            day = rest[1] if len(rest) > 1 else 1
            try:
                return date(int(year), int(month), int(day)).isoformat()
            except ValueError:
                continue
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref work-list response into the stable raw-record contract."""
    records: list[PaperRecord] = []
    seen_ids: set[str] = set()
    for item in payload.get("message", {}).get("items", []):
        paper_id = _clean_text(item.get("DOI")).lower()
        titles = item.get("title") or []
        title = _clean_text(titles[0] if titles else "")
        if not paper_id or not title or paper_id in seen_ids:
            continue

        authors = [
            normalize_whitespace(" ".join(filter(None, [author.get("given"), author.get("family")])))
            for author in item.get("author", [])
            if normalize_whitespace(" ".join(filter(None, [author.get("given"), author.get("family")])))
        ]
        categories = [_clean_text(subject) for subject in item.get("subject", []) if _clean_text(subject)]
        published = _crossref_date(item)
        updated = _clean_text(item.get("created", {}).get("date-time")) or published
        url = _clean_text(item.get("URL")) or f"https://doi.org/{paper_id}"
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_clean_text(item.get("abstract")) or "Abstract unavailable from Crossref.",
                authors=authors or ["Unknown author"],
                categories=categories or ["Uncategorized"],
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {paper_id}",
            )
        )
        seen_ids.add(paper_id)
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref with a deterministic local-snapshot fallback for reproducibility."""
    snapshot = settings.paths.raw_api_response
    payload: dict[str, Any] | None = None

    if not settings.refresh_source and snapshot.exists():
        payload = read_json(snapshot)
    else:
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
            "select": "DOI,title,abstract,author,subject,published,created,URL",
        }
        for attempt in range(3):
            try:
                response = requests.get("https://api.crossref.org/works", params=params, timeout=20)
                if response.status_code in {429, 503}:
                    time.sleep(2**attempt)
                    continue
                response.raise_for_status()
                payload = response.json()
                write_json(snapshot, payload)
                break
            except requests.RequestException:
                if attempt == 2:
                    break
                time.sleep(2**attempt)

    if payload is None:
        if not snapshot.exists():
            raise RuntimeError("Crossref fetch failed and no local snapshot is available.")
        payload = read_json(snapshot)

    records = parse_crossref_payload(payload)
    if not records:
        raise RuntimeError("Crossref payload did not contain usable records.")
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load the persisted raw-record artifact without altering lineage data."""
    rows = read_json(path)
    return [
        PaperRecord(
            paper_id=str(row["paper_id"]),
            title=str(row["title"]),
            summary=str(row.get("summary", "")),
            authors=[str(item) for item in row.get("authors", [])],
            categories=[str(item) for item in row.get("categories", [])],
            primary_category=str(row.get("primary_category", "Uncategorized")),
            published=str(row.get("published", "")),
            updated=str(row.get("updated", "")),
            abs_url=str(row.get("abs_url", "")),
            pdf_url=str(row.get("pdf_url", "")),
            comment=str(row.get("comment", "")),
        )
        for row in rows
    ]
