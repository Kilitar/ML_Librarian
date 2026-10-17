from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data/normalized/chunks_curated.jsonl"
QUESTIONS = ROOT / "eval/retrieval_questions.json"
OUT = ROOT / "eval/retrieval_curated_full_results.json"
CACHE = ROOT / ".cache" / "hf"
MODEL = "intfloat/multilingual-e5-small"


def main() -> None:
    docs = [json.loads(line) for line in CHUNKS.open(encoding="utf-8") if line.strip()]
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8-sig"))
    texts = [doc["text"] for doc in docs]
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), sublinear_tf=True, max_features=100_000,
        token_pattern=r"(?u)\b\w+\b",
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    torch.set_num_threads(min(8, torch.get_num_threads()))
    model = SentenceTransformer(MODEL, cache_folder=str(CACHE), device="cpu")
    passages = model.encode(
        ["passage: " + text for text in texts], batch_size=96,
        show_progress_bar=True, normalize_embeddings=True, convert_to_numpy=True,
    )
    qvecs = model.encode(
        ["query: " + q["query"] for q in questions], batch_size=16,
        show_progress_bar=False, normalize_embeddings=True, convert_to_numpy=True,
    )
    results = []
    for qi, question in enumerate(questions):
        gold = question["gold_source_paths"]
        row = {
            "id": question["id"], "query": question["query"],
            "language": question["query_language"], "gold_paths": gold,
            "gold_present_in_corpus": any(doc["source_path"] in gold for doc in docs),
            "retrievers": {},
        }
        scores_by_model = {
            "tfidf": cosine_similarity(vectorizer.transform([question["query"]]), tfidf_matrix).ravel(),
            "e5": passages @ qvecs[qi],
        }
        for name, scores in scores_by_model.items():
            top = np.argsort(scores)[-5:][::-1]
            rank = next((r + 1 for r, i in enumerate(top) if docs[int(i)]["source_path"] in gold), None)
            row["retrievers"][name] = {
                "gold_rank_at_5": rank,
                "reciprocal_rank_at_5": 0 if rank is None else 1 / rank,
                "top5": [
                    {"source_path": docs[int(i)]["source_path"],
                     "locator": docs[int(i)].get("locator"), "score": float(scores[int(i)]),
                     "text": docs[int(i)]["text"][:220]}
                    for i in top
                ],
            }
        results.append(row)

    summary = {}
    for name in ("tfidf", "e5"):
        rows = [r["retrievers"][name] for r in results if r["gold_present_in_corpus"]]
        summary[name] = {
            "queries_with_gold_in_corpus": len(rows),
            "mrr_at_5": float(np.mean([r["reciprocal_rank_at_5"] for r in rows])) if rows else None,
            "recall_at_5": float(np.mean([r["gold_rank_at_5"] is not None for r in rows])) if rows else None,
        }
    output = {
        "scope": "Full curated instructional-text corpus; page-level provisional gold labels",
        "model": MODEL, "queries": len(questions), "passages": len(docs),
        "metrics_exclude_queries_without_gold_in_corpus": True,
        "summary": summary, "results": results,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
