from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Create a fixed 10-question benchmark spanning the four required question types."""
    if len(df) < 10:
        raise ValueError("At least 10 documents are required to build the evaluation set.")
    ordered = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    # Spread questions across the corpus so loss of recent documents is measurable.
    positions = [0, 2, 5, 7, 9, 11, 14, 16, 19, len(ordered) - 1]
    rows = [ordered.iloc[min(position, len(ordered) - 1)] for position in positions]
    question_types = ["summary", "authors", "date", "categories", "summary", "authors", "date", "categories", "summary", "authors"]
    templates = {
        "summary": "Summarize the paper '{title}'.",
        "authors": "Who authored the paper '{title}'?",
        "date": "When was the paper '{title}' published on?",
        "categories": "What categories does the paper '{title}' belong to?",
    }
    test_set: list[dict[str, Any]] = []
    for number, (row, question_type) in enumerate(zip(rows, question_types, strict=True), start=1):
        references = {
            "summary": first_sentence(str(row["summary"])),
            "authors": str(row["authors_joined"]),
            "date": str(row["published"]),
            "categories": str(row["categories_joined"]),
        }
        test_set.append(
            {
                "id": f"q{number:02d}",
                "question_type": question_type,
                "question": templates[question_type].format(title=row["title"]),
                "ground_truth": references[question_type],
                "ground_truth_doc_ids": [str(row["paper_id"])],
            }
        )
    write_json(output_path, test_set)
    return test_set
