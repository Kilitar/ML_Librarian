"""Render frozen evidence and provisional judgments for learner review."""
import argparse
import html
import json
from pathlib import Path

from score_quality import score

ROOT = Path(__file__).resolve().parents[2]


def render(results: dict, judgments: dict) -> str:
    metrics = score(results, judgments)  # Reject stale or incomplete judgments.
    escape = html.escape
    page = '''<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Librarian · kontrola relevance</title><style>:root{color-scheme:light dark}body{font:16px/1.5 system-ui;max-width:1100px;margin:32px auto;padding:0 24px}
section{border-top:2px solid #8886;padding-top:20px;margin-top:32px}article{border:1px solid #8886;border-radius:10px;padding:16px;margin:16px 0}
pre{font:14px/1.5 monospace;white-space:pre-wrap;overflow-wrap:anywhere}h3,small{overflow-wrap:anywhere}small{opacity:.8}
.grade{font-weight:bold}blockquote{margin:12px 0;padding:12px;border-left:4px solid #789}button,summary{cursor:pointer}button{padding:8px 16px}a{color:light-dark(#165bb5,#9ec9ff)}</style>
<h1>ML Librarian: kontrola relevance</h1><p>Moje předběžné hodnocení konkrétních úryvků, bez nezávislého potvrzení. Skóre relevance není pravděpodobnost správnosti.
V této sadě se ranking během měření neměnil. Po kontrole už jde o vývojovou sadu.</p>
<p>2 = přímo užitečné; 1 = související nebo nedostatečné; 0 = nepodporuje požadavek. I užitečný úryvek může vyžadovat další kontext.</p>
<p><a href="http://localhost:8766/" target="_blank">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>'''
    page += (f'<p>Kurzové dotazy: {metrics["answerable_queries"]}; Hit@5 {metrics["hit_at_5"]:.3f}; '
             f'MRR@5 {metrics["mrr_at_5"]:.3f}; Precision@5 {metrics["precision_at_5"]:.3f}. '
             'Nejde o corpus-wide recall ani kontrolu úplných odpovědí.</p>')
    labels = {2: "Přímo užitečné", 1: "Související / nedostatečné", 0: "Nepodporuje požadavek"}
    for question in results["results"]:
        page += (f'<section><h2>{escape(question["id"])}</h2><blockquote>{escape(question["query"])}</blockquote>'
                 '<button onclick="navigator.clipboard.writeText(this.parentElement.querySelector(\'blockquote\').innerText)">Kopírovat dotaz</button>'
                 f'<p><b>Požadovaný důkaz:</b> {escape(question["required_evidence"])}</p>')
        for rank, (passage, judgment) in enumerate(zip(question["top5"], judgments["queries"][question["id"]]), 1):
            page += (f'<article><h3>{rank}. {escape(passage["source_path"])}</h3>'
                     f'<p class="grade">{judgment["grade"]} — {labels[judgment["grade"]]}</p>'
                     f'<p>{escape(judgment["reason"])}</p><small>Relevance {passage["ranking_score"]:.3f} · '
                     f'{escape(str(passage.get("locator") or ""))} · Chunk {escape(passage["chunk_id"])}</small>'
                     f'<details{" open" if rank == 1 else ""}><summary>Celý úryvek</summary><pre>{escape(passage["text"])}</pre></details></article>')
        page += '</section>'
    return page + '</html>'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=("quality", "holdout_v1"), default="holdout_v1")
    args = parser.parse_args()
    results = json.loads((ROOT / f"eval/{args.set}_results.local.json").read_text(encoding="utf-8"))
    judgments = json.loads((ROOT / f"eval/{args.set}_judgments.json").read_text(encoding="utf-8"))
    target = ROOT / f"eval/{args.set}_review.local.html"
    target.write_text(render(results, judgments), encoding="utf-8")
    print(f"http://localhost:8765/eval/{target.name}")


if __name__ == "__main__":
    main()
