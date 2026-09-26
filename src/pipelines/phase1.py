from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def run_phase1_pipeline(settings=None) -> dict:
    """Run the reproducible clean-data baseline from raw Crossref lineage to report."""
    settings = settings or load_settings()
    records = fetch_source_records(settings)
    clean_df = build_clean_dataframe(records, now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    build_test_set(clean_df, settings.paths.eval_testset)
    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    evaluation = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    quality = run_data_quality_checks(clean_df, settings, "baseline")
    demo = [
        answer_question(item["question"], settings, index).__dict__
        for item in __import__("core.utils", fromlist=["read_json"]).read_json(settings.paths.eval_testset)[:2]
    ]
    write_json(settings.paths.demo_answers, demo)
    generate_phase1_report(
        settings.paths.baseline_report,
        {
            "source": settings.source_api,
            "records": len(records),
            "clean_records": len(clean_df),
            "embedding_model": settings.embedding_model,
            "collection_name": settings.baseline_collection_name,
        },
        evaluation.summary,
        quality,
        quality["freshness"],
    )
    print(f"Baseline complete: {len(clean_df)} clean documents")
    print(f"Metrics: {evaluation.summary}")
    print(f"Quality gate: {quality['success']}; freshness: {quality['freshness']['is_fresh']}")
    return {
        "records": len(records),
        "clean_records": len(clean_df),
        "metrics": evaluation.summary,
        "quality": quality,
    }


def main() -> None:
    run_phase1_pipeline()


if __name__ == "__main__":
    main()
