"""Freeze evidence availability decisions, including fresh and ambiguous queries."""
import hashlib
import html
import json
from pathlib import Path
from datetime import datetime, timezone
from search import E5SearchIndex, MANIFEST
from evidence_gate import assess_evidence, POLICY_VERSION, LOW_SUPPORT, SUFFICIENT_SUPPORT

ROOT = Path(__file__).resolve().parents[2]
FILES = ('search.py', 'rerank.py', 'evidence_gate.py', 'constraints.py', 'diversify.py', 'hybrid.py', 'chunk_text.py', 'acronyms.py', 'snippet_format.py', 'concepts.py', 'semantic_layer.py', 'domain_concepts.json', 'comparisons.py', 'source_filters.py')


def main():
    old = json.loads((ROOT / 'eval/reliability_comparison.local.json').read_text(encoding='utf-8'))
    fresh_path = ROOT / 'eval/abstention_fresh_questions.json'
    fresh = json.loads(fresh_path.read_text(encoding='utf-8'))
    questions = [{**q, 'split': 'regression', 'expected': 'supported' if q['answerable'] else 'no_support'} for q in old['results']]
    questions += [{**q, 'split': 'fresh'} for q in fresh]
    hashes = {name: hashlib.sha256((ROOT / 'src/librarian' / name).read_bytes()).hexdigest() for name in FILES}
    index = E5SearchIndex.load()
    rows = []
    for q in questions:
        results = index.search(q['query'], mode='rerank')
        decision = assess_evidence(results, q['query'])
        rows.append({key: value for key, value in q.items() if key not in {'before','after'}} |
                    {'decision': decision, 'results': results})
        print(q['id'], 'expected', q['expected'], 'actual', decision['status'], decision['score'], flush=True)
    if hashes != {name: hashlib.sha256((ROOT / 'src/librarian' / name).read_bytes()).hexdigest() for name in FILES}:
        raise RuntimeError('Ranking/policy changed during evaluation')
    output = {'created_at': datetime.now(timezone.utc).isoformat(), 'source_hashes': hashes,
              'fresh_questions_sha256': hashlib.sha256(fresh_path.read_bytes()).hexdigest(),
              'policy': POLICY_VERSION, 'low': LOW_SUPPORT, 'sufficient': SUFFICIENT_SUPPORT,
              'index_manifest': json.loads(MANIFEST.read_text(encoding='utf-8')), 'results': rows}
    (ROOT / 'eval/abstention_results.local.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    page = '''<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Librarian · opora dotazů</title>
<style>:root{color-scheme:light dark}body{font:16px/1.5 system-ui;max-width:1100px;margin:32px auto;padding:0 24px}section{border-top:1px solid #8886;margin:24px 0;padding-top:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #8886;text-align:left}a{color:light-dark(#165bb5,#9ec9ff)}</style>
<h1>Ověření opory dotazů</h1><p>Signál opory neověřuje pravdivost ani úplnost zdrojů. „Nenašel jsem dostatečnou oporu“ neznamená důkaz, že žádná informace neexistuje. Skóre není kalibrovaná pravděpodobnost.</p><p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p><table><tr><th>Dotaz</th><th>Sada</th><th>Očekáváno</th><th>Výsledek</th></tr>'''
    for q in rows:
        page += f'<tr><td><a href="#{html.escape(q["id"])}">{html.escape(q["query"])}</a></td><td>{q["split"]}</td><td>{q["expected"]}</td><td>{q["decision"]["status"]}</td></tr>'
    page += '</table>'
    for q in rows:
        page += f'<section id="{html.escape(q["id"])}"><h2>{html.escape(q["query"])}</h2><p>{q["decision"]["status"]} · signál {q["decision"]["score"]}</p>'
        for p in q['results']:
            page += f'<details><summary>{html.escape(p["source_path"])} · celé skóre {p.get("whole_query_score", "unknown")}</summary><pre>{html.escape(p["text"])}</pre></details>'
        page += '</section>'
    (ROOT / 'eval/abstention_review.local.html').write_text(page+'</html>',encoding='utf-8')
    print('http://localhost:8765/eval/abstention_review.local.html')


if __name__ == '__main__':
    main()
