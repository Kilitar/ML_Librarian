"""Score reviewed top-five passages; this is not corpus-wide recall."""
from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]


def score(results: dict, judgments: dict) -> dict:
    if results.get("ranking_files_sha256") != judgments.get("ranking_files_sha256"):
        raise ValueError("Review mismatch: ranking helper files")
    for key in ("questions_sha256", "search_sha256"):
        if results[key] != judgments[key]:
            raise ValueError(f"Review mismatch: {key}")
    if results["index_manifest"]["corpus_fingerprint"] != judgments["corpus_fingerprint"]:
        raise ValueError("Review refers to a different corpus")
    rows = []
    if {q["id"] for q in results["results"]} != set(judgments["queries"]):
        raise ValueError("Question coverage differs from review")
    for question in results["results"]:
        review = judgments["queries"][question["id"]]
        if len(review) != 5 or len(question["top5"]) != 5:
            raise ValueError("Every question needs five reviewed passages")
        grades = []
        for passage, judgment in zip(question["top5"], review):
            digest = hashlib.sha256(passage["text"].encode("utf-8")).hexdigest()
            if passage["chunk_id"] != judgment["chunk_id"] or digest != judgment["text_sha256"]:
                raise ValueError("Passage order or text differs from review")
            grade = judgment["grade"]
            if grade not in (0, 1, 2):
                raise ValueError("Unknown relevance grade")
            grades.append(grade)
        first = next((rank for rank, grade in enumerate(grades, 1) if grade == 2), None)
        rows.append({"id": question["id"], "answerable": question["answerable"],
                     "first_useful_rank": first, "precision_at_5": grades.count(2) / 5,
                     "reciprocal_rank_at_5": 1 / first if first else 0,
                     "top1_useful": grades[0] == 2})
    answerable = [row for row in rows if row["answerable"]]
    absent = [row for row in rows if not row["answerable"]]
    return {
        "reviewer": judgments["reviewer"],
        "answerable_queries": len(answerable),
        "hit_at_5": mean(row["first_useful_rank"] is not None for row in answerable),
        "mrr_at_5": mean(row["reciprocal_rank_at_5"] for row in answerable),
        "precision_at_5": mean(row["precision_at_5"] for row in answerable),
        "top1_useful_rate": mean(row["top1_useful"] for row in answerable),
        "unanswerable_queries": len(absent),
        "unanswerable_with_useful_evidence": sum(row["first_useful_rank"] is not None for row in absent),
        "per_query": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=("quality", "holdout_v1"), default="quality")
    args = parser.parse_args()
    results = json.loads((ROOT / f"eval/{args.set}_results.local.json").read_text(encoding="utf-8"))
    judgments = json.loads((ROOT / f"eval/{args.set}_judgments.json").read_text(encoding="utf-8"))
    print(json.dumps(score(results, judgments), ensure_ascii=False, indent=2))
