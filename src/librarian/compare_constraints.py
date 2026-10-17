"""Reproduce both ranking variants and generate a local side-by-side review."""
from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from search import E5SearchIndex, MANIFEST

ROOT = Path(__file__).resolve().parents[2]


def render_card(rank: int, passage: dict) -> str:
    escape = html.escape
    text = passage["text"]
    preview = text[:320] + ("…" if len(text) > 320 else "")
    return (
        f'<article><h4>{rank}. {escape(passage["source_path"])}</h4>'
        f'<small>Relevance {passage["ranking_score"]:.3f} · '
        f'E5 {passage["score"]:.3f} · {escape(str(passage.get("locator") or ""))}</small>'
        f'<p class="excerpt">{escape(preview)}</p>'
        f'<details><summary>Celý úryvek</summary><pre>{escape(text)}</pre></details>'
        f'<small>Chunk: {escape(passage["chunk_id"])}</small></article>'
    )


def main() -> None:
    questions_path = ROOT / "eval/quality_questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    index = E5SearchIndex.load()
    rows = []
    sections = []
    for question in questions:
        before = index.search(question["query"], match_constraints=False)
        after = index.search(question["query"])
        rows.append({**question, "before": before, "after": after})
        columns = "".join(
            f'<div><h3>{title}</h3>' + "".join(render_card(rank, p) for rank, p in enumerate(passages, 1)) + '</div>'
            for title, passages in (("Před úpravou", before), ("Po úpravě", after))
        )
        sections.append(
            f'<section><h2>{html.escape(question["id"])}</h2><blockquote>{html.escape(question["query"])}</blockquote>'
            '<button onclick="navigator.clipboard.writeText(this.parentElement.querySelector(\'blockquote\').innerText)">Kopírovat dotaz</button>'
            f'<div class="columns">{columns}</div></section>'
        )
        print(question["id"], "complete", flush=True)
    output = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "index_manifest": json.loads(MANIFEST.read_text(encoding="utf-8")),
        "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in ("src/librarian/search.py", "src/librarian/constraints.py", "src/librarian/diversify.py", "src/librarian/chunk_text.py", "eval/quality_questions.json")},
        "results": rows,
    }
    (ROOT / "eval/quality_comparison.local.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    page = '''<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Librarian · porovnání vyhledávání</title><style>
:root{color-scheme:light dark}body{font:16px/1.5 system-ui;max-width:1400px;margin:32px auto;padding:0 24px}
a{color:light-dark(#165bb5,#9ec9ff)}section{border-top:2px solid #8886;margin-top:36px;padding-top:16px}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:24px}article{border:1px solid #8886;border-radius:10px;padding:16px;margin-bottom:16px}
h4{margin:0 0 8px;overflow-wrap:anywhere}small{opacity:.75;overflow-wrap:anywhere}.excerpt,pre{white-space:pre-wrap;overflow-wrap:anywhere}
pre{font:inherit}blockquote{margin:12px 0;padding:12px 16px;border-left:4px solid #789;background:#8881}
button{padding:8px 16px;cursor:pointer}summary{cursor:pointer}@media(max-width:800px){.columns{grid-template-columns:1fr}}
</style><h1>ML Librarian: výsledky před / po</h1>
<p>Stejný index a dotazy. Vlevo původní ranking, vpravo přidaná shoda algoritmu a datasetu.
Jde o vývojovou sadu, nikoli nezávislý závěrečný benchmark. Skóre není pravděpodobnost správnosti.</p>
<p><a href="http://localhost:8766/" target="_blank">Otevřít Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>'''
    (ROOT / "eval/quality_comparison.local.html").write_text(page + "".join(sections) + "</html>", encoding="utf-8")
    print("Review: http://localhost:8765/eval/quality_comparison.local.html")


if __name__ == "__main__":
    main()
