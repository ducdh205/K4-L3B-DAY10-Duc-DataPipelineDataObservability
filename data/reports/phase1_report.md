# Phase 1 — Baseline Pipeline Report

## Source and lineage

| Signal | Value |
| --- | --- |
| Source | Crossref REST API |
| Raw records | 24 |
| Clean records | 24 |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Collection | papers-baseline |

## Evaluation

| Metric | Value |
| --- | ---: |
| Retrieval hit rate | 1.0000 |
| Mean token F1 | 1.0000 |
| Judge accuracy | 1.0000 |
| Mean judge score | 5 |

## Data Quality and Freshness

- Great Expectations 1.x quality gate: **PASS**
- Freshness SLA (at most 25% older than 180 days): **PASS**
- Stale records: 1/24 (4.2%)
- Publication range: 2026-03-28 to 2026-07-22
