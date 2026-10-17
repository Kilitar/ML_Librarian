"""Paired domain-layer ablation on fixed multilingual definition questions."""
import hashlib
import html
import json
from pathlib import Path
from search import E5SearchIndex
from evidence_gate import assess_evidence
from semantic_layer import VERSION, FINGERPRINT

ROOT = Path(__file__).resolve().parents[2]
# Fixed before the first run; these become development/regression questions.
QUESTIONS = [
    ('deep_learning', ['Co je hluboké učení', 'What is deep learning?', 'Czym jest głębokie uczenie?']),
    ('machine_learning', ['Co je strojové učení', 'What is machine learning?', 'Co to jest uczenie maszynowe?']),
    ('neural_networks', ['Co jsou neuronové sítě', 'What are neural networks?', 'Czym są sieci neuronowe?']),
    ('overfitting', ['Co je přeučení', 'What is overfitting?', 'Co to jest przeuczenie?']),
    ('regression', ['Co je regrese', 'What is regression?', 'Co to jest regresja?']),
    ('classification', ['Co je klasifikace', 'What is classification?', 'Co to jest klasyfikacja?']),
]


def main():
    index = E5SearchIndex.load()
    rows = []
    for concept, queries in QUESTIONS:
        for query in queries:
            variants = {}
            for enabled in (False, True):
                results = index.search(query, mode='rerank', semantic_layer=enabled, semantic_experiment=True)
                if not results or any(r['retrieval_mode'] != 'rerank' for r in results):
                    raise RuntimeError('Ablation cannot silently use fallback')
                variants['layer' if enabled else 'baseline'] = {
                    'decision': assess_evidence(results, query), 'results': results}
            rows.append({'concept': concept, 'query': query, **variants})
            print(query, variants['baseline']['decision']['status'], '->', variants['layer']['decision']['status'], flush=True)
    consistency = {}
    for concept, _ in QUESTIONS:
        group = [r for r in rows if r['concept'] == concept]
        consistency[concept] = {v: len({tuple(p['chunk_id'] for p in r[v]['results']) for r in group}) == 1
                                for v in ('baseline', 'layer')}
    result = {'version': VERSION, 'vocabulary_sha256': FINGERPRINT, 'consistency': consistency,
              'scope': 'Baseline retains shared query-intent/source priors and algorithm/dataset constraints. Not a pure-model comparison. No human usefulness judgments or accuracy metric.',
              'code_sha256': {n: hashlib.sha256((Path(__file__).parent / n).read_bytes()).hexdigest()
                              for n in ('search.py','semantic_layer.py','concepts.py','evidence_gate.py','rerank.py')},
              'rows': rows}
    (ROOT / 'eval/semantic_comparison.local.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    parts = ['<!doctype html><meta charset="utf-8"><title>Sémantická vrstva – porovnání</title><style>body{font:16px system-ui;background:#111827;color:#eee;margin:30px}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}pre{white-space:pre-wrap;background:#1f2937;padding:12px}details{margin:12px 0}</style><h1>Doménová vrstva zapnutá / vypnutá</h1><p>18 pevných dotazů, stejný index a modely. Základ zachovává společná pravidla pro záměr, zdroj a algoritmy/datasety. Shodné pořadí neznamená správnou odpověď. Bez nezávislého hodnocení užitečnosti.</p>', '<pre>'+html.escape(json.dumps(consistency, ensure_ascii=False, indent=2))+'</pre>']
    for row in rows:
        parts.append('<h2>'+html.escape(row['query'])+'</h2><main>')
        for variant, label in (('baseline', 'Bez doménové vrstvy'), ('layer', 'S doménovou vrstvou')):
            parts.append('<section><h3>'+label+'</h3><p>'+html.escape(str(row[variant]['decision']))+'</p>')
            for rank, p in enumerate(row[variant]['results'], 1):
                parts.append('<details'+(' open' if rank == 1 else '')+'><summary>'+str(rank)+'. '+html.escape(p['source_path'])+'</summary><pre>'+html.escape(p['text'])+'</pre></details>')
            parts.append('</section>')
        parts.append('</main>')
    parts.insert(1, '<p><strong>Experimental rewrites: regression and classification are not enabled in production due to observed passage regressions. Production enables deep learning, machine learning, neural networks and overfitting only.</strong></p>')
    (ROOT / 'eval/semantic_comparison.local.html').write_text('\n'.join(parts), encoding='utf-8')
    print(json.dumps(consistency), flush=True)


if __name__ == '__main__':
    main()
