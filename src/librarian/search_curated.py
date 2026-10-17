from __future__ import annotations

import argparse
import json

from search import E5SearchIndex
from evidence_gate import assess_evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the local curated course corpus with multilingual E5")
    parser.add_argument("query", nargs="+", help="Question or search phrase in Czech, English, or Polish")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--mode", choices=("e5", "hybrid", "rerank"), default="rerank",
                        help="production uses rerank; e5 is the offline fallback, hybrid remains experimental")
    parser.add_argument("--show-weak", action="store_true", help="Include weak matches when support was not found")
    args = parser.parse_args()
    results = E5SearchIndex.load().search(" ".join(args.query), limit=args.limit, mode=args.mode)
    evidence = assess_evidence(results, " ".join(args.query))
    if evidence["status"] == "no_support":
        print("V materiálech jsem nenašel dostatečnou oporu pro tento dotaz.")
        if not args.show_weak:
            return
    elif evidence["status"] == "uncertain":
        print("Opora je nejistá; následují orientační pasáže. Upřesni téma, algoritmus nebo dataset.")
    elif evidence["status"] == "unassessed":
        print("Oporu dotazu nelze ověřit; následují základní podobné pasáže.")
    for rank, result in enumerate(results, 1):
        print(
            f"{rank}. relevance={result['ranking_score']:.3f} "
            f"(semantic={result['score']:.3f}) | {result['source_path']} | {result['locator']}"
        )
        print(f"   chunk={result['chunk_id']} | language={result['language']} | {result['provenance']}")
        if result["streamlit_route"]:
            print(f"   route={result['streamlit_route']} ({result['route_status']})")
        print("   " + json.dumps(result["text"], ensure_ascii=False))


if __name__ == "__main__":
    main()
