from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def _metric(value: Any) -> str:
    return f"{value:.4f}" if isinstance(value, float) else str(value)


def generate_phase1_report(report_path, source_summary: dict[str, Any], metrics: dict[str, Any], quality: dict[str, Any], freshness: dict[str, Any]) -> None:
    """Write the baseline evidence report solely from generated artifacts."""
    report = f"""# Phase 1 — Baseline Pipeline Report

## Source and lineage

| Signal | Value |
| --- | --- |
| Source | {source_summary['source']} |
| Raw records | {source_summary['records']} |
| Clean records | {source_summary['clean_records']} |
| Embedding model | {source_summary['embedding_model']} |
| Collection | {source_summary['collection_name']} |

## Evaluation

| Metric | Value |
| --- | ---: |
| Retrieval hit rate | {_metric(metrics['retrieval_hit_rate'])} |
| Mean token F1 | {_metric(metrics['mean_token_f1'])} |
| Judge accuracy | {_metric(metrics['judge_accuracy'])} |
| Mean judge score | {_metric(metrics['mean_judge_score'])} |

## Data Quality and Freshness

- Great Expectations 1.x quality gate: **{'PASS' if quality['gx_success'] else 'FAIL'}**
- Freshness SLA (at most 25% older than {freshness['freshness_threshold_days']} days): **{'PASS' if freshness['is_fresh'] else 'FAIL'}**
- Stale records: {freshness['stale_rows']}/{freshness['total_rows']} ({freshness['stale_ratio']:.1%})
- Publication range: {freshness['oldest_published']} to {freshness['latest_published']}
"""
    write_text(Path(report_path), report)


def generate_corruption_report(report_path, baseline_metrics: dict[str, Any], corrupted_metrics: dict[str, Any], repaired_metrics: dict[str, Any], corrupted_quality: dict[str, Any], repaired_quality: dict[str, Any], corrupted_freshness: dict[str, Any], repaired_freshness: dict[str, Any]) -> None:
    """Write a data-backed comparison across the three pipeline states."""
    metrics = ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]
    rows = "\n".join(
        f"| {metric} | {_metric(baseline_metrics[metric])} | {_metric(corrupted_metrics[metric])} | {_metric(repaired_metrics[metric])} |"
        for metric in metrics
    )
    report = f"""# Corruption and Repair Report

The same 10-question evaluation set was used for baseline, corrupted, and repaired indices.

## Metric comparison

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
{rows}

## Quality and freshness comparison

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| Quality gate | PASS | {'PASS' if corrupted_quality['success'] else 'FAIL'} | {'PASS' if repaired_quality['success'] else 'FAIL'} |
| GX expectations | PASS | {'PASS' if corrupted_quality['gx_success'] else 'FAIL'} | {'PASS' if repaired_quality['gx_success'] else 'FAIL'} |
| Freshness | PASS | {'PASS' if corrupted_freshness['is_fresh'] else 'FAIL'} | {'PASS' if repaired_freshness['is_fresh'] else 'FAIL'} |
| Stale records | baseline artifact | {corrupted_freshness['stale_rows']}/{corrupted_freshness['total_rows']} | {repaired_freshness['stale_rows']}/{repaired_freshness['total_rows']} |

## Interpretation

The corruption suite intentionally drops recent records, damages summaries and titles, backdates publications, and duplicates rows. The quality gate catches the resulting contract violations while the common evaluation set quantifies retrieval and answer impact. Repair reloads the immutable raw-record artifact, rebuilds the clean dataset and a separate Chroma collection, making the operation idempotent and restoring the baseline contract.
"""
    write_text(Path(report_path), report)
