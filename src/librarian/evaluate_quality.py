"""Freeze top-five evidence from the production retriever for passage-level review.

No embedding rebuild, API call, or ranking changes. Run before inspecting results.
"""
from __future__ import annotations

import hashlib
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from search import E5SearchIndex, MANIFEST

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=("quality", "holdout_v1"), default="quality")
    parser.add_argument("--mode", choices=("e5", "hybrid", "rerank"), default="rerank")
    args = parser.parse_args()
    questions_path = ROOT / f"eval/{args.set}_questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    index = E5SearchIndex.load()
    rows = []
    for question in questions:
        results = index.search(question["query"], limit=5, mode=args.mode)
        if any(result["retrieval_mode"] != args.mode for result in results):
            raise RuntimeError("Evaluation cannot silently count fallback as requested retrieval mode")
        rows.append({**question, "top5": results})
        print(question["id"], "complete", flush=True)
    output = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retrieval_mode": args.mode,
        "questions_sha256": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
        "search_sha256": hashlib.sha256((ROOT / "src/librarian/search.py").read_bytes()).hexdigest(),
        "ranking_files_sha256": {
            "source_filters.py": hashlib.sha256((ROOT / "src/librarian/source_filters.py").read_bytes()).hexdigest(),
            "comparisons.py": hashlib.sha256((ROOT / "src/librarian/comparisons.py").read_bytes()).hexdigest(),
            "semantic_layer.py": hashlib.sha256((ROOT / "src/librarian/semantic_layer.py").read_bytes()).hexdigest(),
            "domain_concepts.json": hashlib.sha256((ROOT / "src/librarian/domain_concepts.json").read_bytes()).hexdigest(),
            "concepts.py": hashlib.sha256((ROOT / "src/librarian/concepts.py").read_bytes()).hexdigest(),
            "acronyms.py": hashlib.sha256((ROOT / "src/librarian/acronyms.py").read_bytes()).hexdigest(),
            "snippet_format.py": hashlib.sha256((ROOT / "src/librarian/snippet_format.py").read_bytes()).hexdigest(),
            "constraints.py": hashlib.sha256((ROOT / "src/librarian/constraints.py").read_bytes()).hexdigest(),
            "diversify.py": hashlib.sha256((ROOT / "src/librarian/diversify.py").read_bytes()).hexdigest(),
            "chunk_text.py": hashlib.sha256((ROOT / "src/librarian/chunk_text.py").read_bytes()).hexdigest(),
            "hybrid.py": hashlib.sha256((ROOT / "src/librarian/hybrid.py").read_bytes()).hexdigest(),
            "rerank.py": hashlib.sha256((ROOT / "src/librarian/rerank.py").read_bytes()).hexdigest(),
        },
        "index_manifest": json.loads(MANIFEST.read_text(encoding="utf-8")),
        "scope": "First-pass unseen topics; becomes a regression set after review. No tuning on this run.",
        "results": rows,
    }
    destination = ROOT / f"eval/{args.set}_results.local.json"
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
