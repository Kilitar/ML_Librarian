"""Offline diagnostic only: domain classification is never imported by search/app."""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut, cross_val_predict

from search import E5SearchIndex, MANIFEST
from evidence_gate import assess_evidence

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / 'eval/domain_probe_training.json'
FRESH = ROOT / 'eval/support_repair_questions.json'
OUTPUT = ROOT / 'eval/domain_probe_results.local.json'
REPORT = ROOT / 'eval/domain_probe_review.local.html'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(data):
    esc = lambda value: html.escape(str(value))
    body = ['<!doctype html><meta charset="utf-8"><title>Domain probe</title>',
            '<style>body{font:16px system-ui;max-width:1100px;margin:40px auto;background:#111827;color:#e5e7eb}article{border:1px solid #64748b;padding:18px;margin:18px 0}pre{white-space:pre-wrap}summary{cursor:pointer}a{color:#93c5fd}</style>',
            '<h1>Doménový klasifikátor: experiment bez nasazení</h1>',
            '<p>Logistická regrese nad neměněnými E5 embeddingy dotazů, C=10, vyvážené třídy, práh 0.5. '
            'Číslo je výstup klasifikátoru, není kalibrovanou pravděpodobností správnosti odpovědi. '
            'Historické štítky dostupnosti opory byly použity jako provizorní doménové štítky. '
            'Kontrola vynechává vždy jednu trénovací otázku; formulace a témata nejsou nezávislé.</p>',
            '<p><b>Produkční vyhledávání ani rozhodovací prahy nebyly změněny. '
            'Pokus neřeší pořadí PCA ani chybějící vysvětlení ceny chyb u spam filtru.</b></p>',
            '<h2>Kontrola na historických otázkách: chyby</h2>']
    for row in data['leave_one_out']:
        if row['predicted_in_domain'] != row['in_domain']:
            body.append(f"<article>{esc(row['query'])}<p>Očekáváno v doméně: {row['in_domain']}; skóre: {row['domain_score']:.3f}</p></article>")
    body.append('<h2>Původní přejímka a nové otázky</h2><p>Každý dotaz má všech pět skutečných výsledků současné produkce. Klasifikátor pouze diagnostikujeme; nemění jejich pořadí ani stav.</p>')
    for row in data['rows']:
        body.append(f"<article><h3>{esc(row['id'])}: {esc(row['query'])}</h3><p>Sada: {esc(row['split'])}; očekávaný stav: {esc(row['expected'])}; produkce: {esc(row['decision']['status'])}; doménové skóre: {row['domain_score']:.3f}</p>")
        for n, result in enumerate(row['results'], 1):
            body.append(f"<details><summary>{n}. {esc(result['source_path'])} · whole-query {result['whole_query_score']:.4f}</summary><p>{esc(result['chunk_id'])} · {esc(result.get('locator'))}</p><pre>{esc(result['text'])}</pre></details>")
        body.append('</article>')
    REPORT.write_text('\n'.join(body), encoding='utf-8')


def main():
    if OUTPUT.exists():
        render(json.loads(OUTPUT.read_text(encoding='utf-8')))
        print('Frozen results preserved; report regenerated.')
        return
    paths = [TRAINING, FRESH, Path(__file__), MANIFEST,
             ROOT / 'src/librarian/search.py', ROOT / 'src/librarian/evidence_gate.py']
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    training = json.loads(TRAINING.read_text(encoding='utf-8'))['questions']
    index = E5SearchIndex.load()
    encode = lambda rows: index.model.encode(['query: ' + r['query'] for r in rows], normalize_embeddings=True, convert_to_numpy=True)
    x = encode(training)
    y = np.asarray([r['in_domain'] for r in training])
    model = LogisticRegression(C=10, class_weight='balanced', random_state=0)
    scores = cross_val_predict(model, x, y, cv=LeaveOneOut(), method='predict_proba')[:, 1]
    loo = [{**r, 'domain_score': float(s), 'predicted_in_domain': bool(s >= .5)} for r, s in zip(training, scores)]
    model.fit(x, y)
    original = json.loads((ROOT / 'eval/acceptance_v1_results.local.json').read_text(encoding='utf-8'))['rows']
    fresh = json.loads(FRESH.read_text(encoding='utf-8'))['questions']
    queries = [{**r, 'split': 'development_acceptance_v1'} for r in original] + [{**r, 'split': 'fresh_formulation'} for r in fresh]
    predictions = model.predict_proba(encode(queries))[:, 1]
    rows = []
    for r, score in zip(queries, predictions):
        # The historical acceptance is immutable; replay its original output.
        results = r.get('results') if r['split'] == 'development_acceptance_v1' else index.search(r['query'], mode='rerank')
        if any(p['retrieval_mode'] != 'rerank' for p in results):
            raise RuntimeError('Unexpected fallback; refuse completed diagnostic')
        decision = r.get('decision') or assess_evidence(results, r['query'])
        rows.append({**r, 'domain_score': float(score), 'results': results, 'decision': decision})
        print(r['id'], decision['status'], round(float(score), 3), flush=True)
    if hashes != {str(p.relative_to(ROOT)): digest(p) for p in paths}:
        raise RuntimeError('Inputs changed during evaluation')
    data = {'created_at': datetime.now(timezone.utc).isoformat(), 'hashes': hashes,
            'model': {'C': 10, 'class_weight': 'balanced', 'threshold': .5, 'encoder': 'intfloat/multilingual-e5-small'},
            'leave_one_out': loo, 'rows': rows, 'production_changed': False}
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    render(data)


if __name__ == '__main__':
    main()
