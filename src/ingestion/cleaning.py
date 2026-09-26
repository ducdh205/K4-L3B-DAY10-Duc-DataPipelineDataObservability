from __future__ import annotations

from datetime import UTC, datetime
import html
import re

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _plain_text(value: str) -> str:
    return normalize_whitespace(re.sub(r"<[^>]+>", " ", html.unescape(value or "")))


def build_embedding_text(row: dict) -> str:
    """Create the canonical five-part document representation used for retrieval."""
    return "\n".join(
        [
            f"Title: {row['title']}",
            f"Authors: {row['authors_joined']}",
            f"Categories: {row['categories_joined']}",
            f"Published: {row['published']}",
            f"Summary: {row['summary']}",
        ]
    )


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Normalize raw Crossref records into an embedding-ready, traceable dataframe."""
    rows: list[dict] = []
    for record in records:
        authors = [_plain_text(author) for author in record.authors if _plain_text(author)]
        categories = [_plain_text(category) for category in record.categories if _plain_text(category)]
        rows.append(
            {
                "paper_id": normalize_whitespace(record.paper_id).lower(),
                "title": _plain_text(record.title),
                "summary": _plain_text(record.summary),
                "authors": authors or ["Unknown author"],
                "categories": categories or ["Uncategorized"],
                "primary_category": _plain_text(record.primary_category) or (categories[0] if categories else "Uncategorized"),
                "published": record.published,
                "updated": record.updated,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": _plain_text(record.comment),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No records supplied for cleaning.")
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df["published"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
    df["updated"] = pd.to_datetime(df["updated"], errors="coerce", utc=True)
    df = df.dropna(subset=["paper_id", "title", "summary", "published"])
    df = df[(df["paper_id"] != "") & (df["title"] != "") & (df["summary"] != "")].copy()

    reference = pd.Timestamp(run_date)
    reference = reference.tz_localize(UTC) if reference.tzinfo is None else reference.tz_convert(UTC)
    df["age_days"] = (reference.normalize() - df["published"].dt.normalize()).dt.days.clip(lower=0)
    df["published"] = df["published"].dt.date.astype(str)
    df["updated"] = df["updated"].dt.date.astype(str)
    df["authors_joined"] = df["authors"].map(compact_join)
    df["categories_joined"] = df["categories"].map(compact_join)
    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = df.apply(lambda row: build_embedding_text(row.to_dict()), axis=1)
    return df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
