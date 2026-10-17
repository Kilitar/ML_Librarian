from __future__ import annotations

import argparse
import json

from search import E5SearchIndex


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the local curated course corpus with multilingual E5")
    parser.add_argument("query", nargs="+", help="Question or search phrase in Czech, English, or Polish")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--mode", choices=("e5", "hybrid"), default="e5",
                        help="hybrid is an experimental development mode; production uses e5")
    args = parser.parse_args()
    results = E5SearchIndex.load().search(" ".join(args.query), limit=args.limit, mode=args.mode)
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
