"""Compare frozen prior evidence and locally reranked passages; include fresh checks."""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from compare_constraints import render_card
from search import E5SearchIndex, MANIFEST
from rerank import MODEL_ID, REVISION

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = ("search.py", "rerank.py", "constraints.py", "diversify.py", "hybrid.py", "chunk_text.py")


def main() -> None:
    previous = json.loads((ROOT / "eval/hybrid_comparison.local.json").read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if previous['index_manifest']['corpus_fingerprint'] != manifest['corpus_fingerprint']:
        raise ValueError('Historical baseline uses a different corpus')
    index = E5SearchIndex.load()
    rows = []
    source_hashes = {name: hashlib.sha256((ROOT / "src/librarian" / name).read_bytes()).hexdigest() for name in SOURCE_FILES}
    fresh = json.loads((ROOT / "eval/reliability_fresh_questions.json").read_text(encoding="utf-8"))
    questions = previous['results'] + [{**q, 'set': 'fresh'} for q in fresh]
    for question in questions:
        before = question.get('before') or index.search(question['query'], mode='e5')
        start = perf_counter()
        after = index.search(question['query'], mode='rerank')
        elapsed = perf_counter() - start
        if any(p['retrieval_mode'] != 'rerank' for p in after):
            raise RuntimeError('Evaluation cannot silently count E5 fallback as reranking')
        rows.append({key: value for key, value in question.items() if key not in {'before', 'after'}} |
                    {'before': before, 'after': after, 'seconds': elapsed})
        print(question['id'], round(elapsed, 2), 's', flush=True)
    if source_hashes != {name: hashlib.sha256((ROOT / "src/librarian" / name).read_bytes()).hexdigest() for name in SOURCE_FILES}:
        raise RuntimeError('Ranking code changed during evaluation')
    output = {'created_at': datetime.now(timezone.utc).isoformat(), 'index_manifest': manifest,
              'source_hashes': source_hashes, 'reranker': {'model': MODEL_ID, 'revision': REVISION},
              'fresh_questions_sha256': hashlib.sha256((ROOT / 'eval/reliability_fresh_questions.json').read_bytes()).hexdigest(),
              'results': rows}
    (ROOT / 'eval/reliability_comparison.local.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    original = (ROOT / 'eval/hybrid_comparison.local.html').read_text(encoding='utf-8')
    style = original[original.index('<style>'):original.index('</style>') + len('</style>')]
    page = '<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Librarian · spolehlivost pasáží</title>' + style
    page += '<h1>Výběr pasáží podle otázky: před / po</h1><p>Vlevo předchozí E5, vpravo kandidáti E5 + TF-IDF posouzení lokálním rerankerem. Nová varianta zahrnuje i doplněné názvy datasetů. Skóre mezi sloupci má jiné měřítko a není pravděpodobností správnosti.</p><p>Prvních 19 otázek je vývojových; posledních 6 bylo připraveno před spuštěním a podle výsledků se ranking neupravoval. Jde o předběžnou kontrolu, nikoli nezávisle potvrzený benchmark.</p><p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>'
    page += '<p>' + ' · '.join(f'<a href="#{html.escape(q["id"])}">{html.escape(q["id"])}</a>' for q in rows) + '</p>'
    for q in rows:
        page += f'<section id="{html.escape(q["id"])}"><h2>{html.escape(q["id"])}</h2><blockquote>{html.escape(q["query"])}</blockquote><small>{html.escape(q["set"])} · nový výběr {q["seconds"]:.2f} s</small><div class="columns">'
        for title, items in (('Předchozí E5', q['before']), ('Nový výběr pasáží', q['after'])):
            page += f'<div><h3>{title}</h3>' + ''.join(render_card(rank, p) for rank, p in enumerate(items, 1)) + '</div>'
        page += '</div></section>'
    (ROOT / 'eval/reliability_comparison.local.html').write_text(page + '</html>', encoding='utf-8')
    print('http://localhost:8765/eval/reliability_comparison.local.html')


if __name__ == '__main__':
    main()
