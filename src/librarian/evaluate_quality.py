"""Freeze top-five evidence from the production retriever for passage-level review.

No embedding rebuild, API call, or ranking changes. Run before inspecting results.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from search import E5SearchIndex, MANIFEST

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    questions_path = ROOT / "eval/quality_questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    index = E5SearchIndex.load()
    rows = []
    for question in questions:
        results = index.search(question["query"], limit=5)
        rows.append({**question, "top5": results})
        print(question["id"], "complete", flush=True)
    output = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "questions_sha256": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
        "search_sha256": hashlib.sha256((ROOT / "src/librarian/search.py").read_bytes()).hexdigest(),
        "ranking_files_sha256": {
            "constraints.py": hashlib.sha256((ROOT / "src/librarian/constraints.py").read_bytes()).hexdigest(),
            "diversify.py": hashlib.sha256((ROOT / "src/librarian/diversify.py").read_bytes()).hexdigest(),
            "chunk_text.py": hashlib.sha256((ROOT / "src/librarian/chunk_text.py").read_bytes()).hexdigest(),
        },
        "index_manifest": json.loads(MANIFEST.read_text(encoding="utf-8")),
        "scope": "First-pass unseen topics; becomes a regression set after review. No tuning on this run.",
        "results": rows,
    }
    destination = ROOT / "eval/quality_results.local.json"
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
