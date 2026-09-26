from __future__ import annotations

from datetime import timedelta
from math import ceil
from pathlib import Path

import pandas as pd

from core.utils import write_json
from ingestion.cleaning import build_embedding_text


def _rebuild_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["summary_chars"] = result["summary"].fillna("").astype(str).str.len()
    result["text_for_embedding"] = result.apply(lambda row: build_embedding_text(row.to_dict()), axis=1)
    return result


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path) -> pd.DataFrame:
    """Inject six deterministic, observable failure modes without mutating the input."""
    if len(df) < 10:
        raise ValueError("At least 10 clean records are required for the corruption suite.")
    result = df.copy().reset_index(drop=True)
    events: list[dict] = []

    latest_count = max(1, ceil(len(result) * 0.20))
    latest_ids = result.sort_values("published", ascending=False).head(latest_count)["paper_id"].tolist()
    result = result[~result["paper_id"].isin(latest_ids)].reset_index(drop=True)
    events.append({"scenario": "drop_latest_records", "affected_paper_ids": latest_ids, "count": len(latest_ids)})

    groups = [
        ("blank_summary", result.index[:3].tolist()),
        ("inject_noise", result.index[3:6].tolist()),
        ("truncate_title", result.index[6:9].tolist()),
        ("stale_date", result.index[9:16].tolist()),
    ]
    for scenario, indexes in groups:
        ids = result.loc[indexes, "paper_id"].tolist()
        if scenario == "blank_summary":
            result.loc[indexes, "summary"] = ""
        elif scenario == "inject_noise":
            result.loc[indexes, "summary"] = "@@@ CORRUPTED_NOISE_!#% " + result.loc[indexes, "summary"].astype(str)
        elif scenario == "truncate_title":
            result.loc[indexes, "title"] = result.loc[indexes, "title"].astype(str).str.slice(0, 7)
        else:
            old_dates = pd.to_datetime(result.loc[indexes, "published"], utc=True)
            stale_dates = old_dates - pd.to_timedelta(365, unit="D")
            result.loc[indexes, "published"] = stale_dates.dt.date.astype(str)
            result.loc[indexes, "age_days"] = result.loc[indexes, "age_days"].astype(int) + 365
        events.append({"scenario": scenario, "affected_paper_ids": ids, "count": len(ids)})

    duplicate_rows = result.iloc[:2].copy()
    result = pd.concat([result, duplicate_rows], ignore_index=True)
    events.append({"scenario": "duplicate_rows", "affected_paper_ids": duplicate_rows["paper_id"].tolist(), "count": len(duplicate_rows)})
    result = _rebuild_derived_columns(result)
    write_json(output_log_path, {"input_rows": len(df), "output_rows": len(result), "scenarios": events})
    return result
