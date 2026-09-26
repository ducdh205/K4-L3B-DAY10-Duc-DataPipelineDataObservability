# Corruption and Repair Report

The same 10-question evaluation set was used for baseline, corrupted, and repaired indices.

## Metric comparison

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| retrieval_hit_rate | 1.0000 | 0.8000 | 1.0000 |
| mean_token_f1 | 1.0000 | 0.6909 | 1.0000 |
| judge_accuracy | 1.0000 | 0.7000 | 1.0000 |
| mean_judge_score | 5 | 3.6000 | 5 |

## Quality and freshness comparison

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| Quality gate | PASS | FAIL | PASS |
| GX expectations | PASS | FAIL | PASS |
| Freshness | PASS | FAIL | PASS |
| Stale records | baseline artifact | 8/21 | 1/24 |

## Interpretation

The corruption suite intentionally drops recent records, damages summaries and titles, backdates publications, and duplicates rows. The quality gate catches the resulting contract violations while the common evaluation set quantifies retrieval and answer impact. Repair reloads the immutable raw-record artifact, rebuilds the clean dataset and a separate Chroma collection, making the operation idempotent and restoring the baseline contract.
