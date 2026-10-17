"""Freeze E5/hybrid development comparisons, with full excerpts for review."""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from compare_constraints import render_card
from search import E5SearchIndex, MANIFEST

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    questions = []
    for name in ("holdout_v1", "quality"):
        questions.extend({**q, "set": name} for q in json.loads((ROOT / f"eval/{name}_questions.json").read_text(encoding="utf-8")))
    questions.append({"id": "reported_kmeans_pl", "set": "learner_feedback", "query": "Kiedy należy zastosować metodę k-średnich", "answerable": True})
    index = E5SearchIndex.load()
    rows = []
    sections = []
    for question in questions:
        before = index.search(question["query"], mode="e5")
        after = index.search(question["query"], mode="hybrid")
        rows.append({**question, "before": before, "after": after})
        columns = "".join(f'<div><h3>{title}</h3>' + "".join(render_card(rank, p) for rank, p in enumerate(passages, 1)) + '</div>'
                          for title, passages in (("E5 + dosavadní přerovnání", before), ("Hybrid + stejné přerovnání", after)))
        sections.append(f'<section id="{html.escape(question["id"])}"><h2>{html.escape(question["id"])}</h2><blockquote>{html.escape(question["query"])}</blockquote>'
                        '<button onclick="navigator.clipboard.writeText(this.parentElement.querySelector(\'blockquote\').innerText)">Kopírovat dotaz</button>'
                        f'<div class="columns">{columns}</div></section>')
        print(question["id"], "complete", flush=True)
    output = {"created_at": datetime.now(timezone.utc).isoformat(),
              "index_manifest": json.loads(MANIFEST.read_text(encoding="utf-8")),
              "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                                ("src/librarian/search.py", "src/librarian/hybrid.py", "src/librarian/constraints.py", "src/librarian/diversify.py")},
              "scope": "Development data already inspected; not a held-out improvement claim.", "results": rows}
    (ROOT / "eval/hybrid_comparison.local.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    page = '''<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Librarian · E5 vs hybrid</title>
<style>:root{color-scheme:light dark}body{font:16px/1.5 system-ui;max-width:1400px;margin:32px auto;padding:0 24px}a{color:light-dark(#165bb5,#9ec9ff)}section{border-top:2px solid #8886;margin-top:36px;padding-top:16px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:24px}article{border:1px solid #8886;border-radius:10px;padding:16px;margin:16px 0}h4{margin:0 0 8px;overflow-wrap:anywhere}small{opacity:.75;overflow-wrap:anywhere}.excerpt,pre{white-space:pre-wrap;overflow-wrap:anywhere}pre{font:inherit}blockquote{margin:12px 0;padding:12px 16px;border-left:4px solid #789;background:#8881}button{padding:8px 16px;cursor:pointer}summary{cursor:pointer}@media(max-width:800px){.columns{grid-template-columns:1fr}}</style>
<h1>E5 versus hybridní vyhledávání</h1><p><strong>Experiment nebyl nasazen jako výchozí: pomohl metrikám, ale zhoršil některé jiné výsledky. Librarian nadále používá E5.</strong></p><p>Stejný korpus, dotazy a pravidla přerovnání. Hybrid spojuje pořadí E5 a TF-IDF; jeho výsledné skóre má jiné měřítko. Skóre mezi sloupci neporovnávej jako jistotu odpovědi.</p>
<p>Jde o vývojové dotazy, které jsme už viděli. Zlepšení zde není nezávislá validace. Celé úryvky rozbalíš u každé položky.</p>
<p><a href="http://localhost:8766/" target="_blank">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>'''
    page += '<p>' + ' · '.join(f'<a href="#{html.escape(q["id"])}">{html.escape(q["id"])}</a>' for q in questions) + '</p>'
    (ROOT / "eval/hybrid_comparison.local.html").write_text(page + "".join(sections) + '</html>', encoding="utf-8")
    print('http://localhost:8765/eval/hybrid_comparison.local.html')


if __name__ == "__main__":
    main()
