from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
from great_expectations.expectations import (
    ExpectColumnValueLengthsToBeBetween,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeBetween,
)
import pandas as pd

from core.config import Settings
from core.utils import write_json


def _quality_report_path(settings: Settings, report_name: str) -> Path:
    known = {
        "baseline": settings.paths.baseline_quality_report,
        "corrupted": settings.paths.corrupted_quality_report,
    }
    return known.get(report_name, settings.paths.quality_dir / f"{report_name}_quality_report.json")


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Measure the freshness SLA independently from schema validation."""
    ages = pd.to_numeric(df.get("age_days"), errors="coerce")
    published = pd.to_datetime(df.get("published"), errors="coerce", utc=True)
    total_rows = int(len(df))
    stale_rows = int((ages > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    payload = {
        "freshness_threshold_days": settings.freshness_threshold_days,
        "latest_published": published.max().date().isoformat() if total_rows and pd.notna(published.max()) else None,
        "oldest_published": published.min().date().isoformat() if total_rows and pd.notna(published.min()) else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "max_stale_ratio": 0.25,
        "is_fresh": bool(total_rows and stale_ratio <= 0.25),
    }
    write_json(Path(report_path), payload)
    return payload


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, stage: str) -> dict[str, Any]:
    """Run a Great Expectations 1.x ephemeral Data Quality Gate and persist evidence."""
    required_columns = {"paper_id", "title", "summary", "text_for_embedding", "age_days"}
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise ValueError(f"Quality checks cannot run; missing columns: {missing_columns}")

    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas(name=f"papers_source_{stage}")
    asset = source.add_dataframe_asset(name=f"papers_asset_{stage}")
    batch_definition = asset.add_batch_definition_whole_dataframe(f"papers_batch_{stage}")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    expectations = [
        ("row_count", ExpectTableRowCountToBeBetween(min_value=5, max_value=5_000)),
        ("paper_id_not_null", ExpectColumnValuesToNotBeNull(column="paper_id")),
        ("title_not_null", ExpectColumnValuesToNotBeNull(column="title")),
        ("text_for_embedding_not_null", ExpectColumnValuesToNotBeNull(column="text_for_embedding")),
        ("paper_id_unique", ExpectColumnValuesToBeUnique(column="paper_id")),
        ("summary_length", ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30, max_value=10_000)),
    ]
    validations = []
    for name, expectation in expectations:
        result = batch.validate(expectation)
        details = dict(result.result or {})
        validations.append(
            {
                "name": name,
                "expectation_type": expectation.expectation_type,
                "success": bool(result.success),
                "unexpected_count": details.get("unexpected_count"),
                "observed_value": details.get("observed_value"),
            }
        )

    freshness_path = settings.paths.freshness_report if stage == "baseline" else settings.paths.quality_dir / f"{stage}_freshness_report.json"
    freshness = build_freshness_report(df, settings, freshness_path)
    gx_success = all(item["success"] for item in validations)
    payload = {
        "report_name": stage,
        "success": bool(gx_success and freshness["is_fresh"]),
        "gx_success": gx_success,
        "freshness_success": freshness["is_fresh"],
        "expectations": validations,
        "freshness": freshness,
    }
    write_json(_quality_report_path(settings, stage), payload)
    return payload
