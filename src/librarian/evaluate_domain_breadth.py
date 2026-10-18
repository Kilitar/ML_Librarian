"""Frozen offline v2 experiment; never imported by production search or gate."""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression

from domain_guard import ENCODER_REVISION, MODEL_ID, load_guard
from evidence_gate import assess_evidence
from search import E5SearchIndex

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'eval/domain_breadth.local.json'
MODEL = ROOT / 'eval/domain_breadth_model.local.json'
REPORT = ROOT / 'eval/domain_breadth_review.local.html'
SUMMARY = ROOT / 'eval/domain_breadth_summary.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_decision(results, query, score):
    baseline = assess_evidence(results, query)
    if not results or baseline['status'] == 'unassessed':
        return baseline
    if baseline.get('reason') == 'ambiguous_query' or any(
        r.get('comparison_aspects') or r.get('semantic_plan') or r.get('requested_acronym')
        or r.get('related_evidence_only') for r in results
    ):
        return baseline
    whole = max(r['whole_query_score'] for r in results)
    threshold = .5 if .10 <= whole < .20 else .2 if whole >= .20 else None
    if threshold is not None and score < threshold:
        return {**baseline, 'status': 'no_support', 'reason': 'experimental_domain_v2',
                'experimental_domain_score': score}
    return baseline


def render(data):
    esc = lambda value: html.escape(str(value))
    page = ['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Širší doménový model: experiment</title>',
            '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}section,article{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary,button{cursor:pointer}a{color:#93c5fd}</style>',
            '<h1>Širší trénink doménového modelu — bez nasazení</h1>',
            '<p>37 historických +72 nových autorských trénovacích otázek. Samostatná logistická regrese C10 balanced nad neměněnými E5 vektory; žádný slovník jídel. Nová kontrola24 formulací fixována před fitováním. Doménové skóre není pravděpodobnost správnosti odpovědi. Témata se překrývají; lidská přejímka neproběhla.</p>',
            '<p>Experimentální odmítnutí: doména&lt;.50 v pásmu [.10,.20), doména&lt;.20 pro silné shody. Strukturální výjimky zachovány. Pořadí, původní skóre, produkční model a aplikace beze změny. Známé případy jsou pouze replay uložených pěti pasáží.</p>',
            '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>',
            '<h2>Předem stanovená kritéria</h2><pre>'+esc(json.dumps(data['checks'], ensure_ascii=False, indent=2))+'</pre>',
            '<p>Splnění kritérií zde samo neznamená nasazení ani nezávislou přejímku. Zelená doména nenahrazuje chybějící oporu; slabé platné otázky zůstávají slabé.</p>']
    for row in data['rows']:
        page.append(f"<section id='{esc(row['id'])}'><h2>{esc(row['id'])} · {esc(row['kind'])}</h2><blockquote>{esc(row['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>{esc(row['split'])} · produkce: <b>{esc(row['before']['status'])}</b> → experiment: <b>{esc(row['after']['status'])}</b><br>Doména v1 {row['domain_v1']:.3f} → v2 {row['domain_v2']:.3f}</p>")
        for n, result in enumerate(row['results'], 1):
            page.append(f"<article><details><summary>{n}. {esc(result['source_path'])} · původní whole-query {result['whole_query_score']:.4f}</summary><p>{esc(result['chunk_id'])} · {esc(result.get('locator'))}</p><pre>{esc(result['text'])}</pre></details></article>")
        page.append('</section>')
    REPORT.write_text('\n'.join(page), encoding='utf-8')


def main():
    if OUTPUT.exists():
        data = json.loads(OUTPUT.read_text(encoding='utf-8'))
        summary = json.loads(SUMMARY.read_text(encoding='utf-8'))
        if summary['raw_sha256'] != digest(OUTPUT):
            raise ValueError('Frozen results hash mismatch')
        render(data)
        print('Frozen results preserved; rendered only.')
        return
    if MODEL.exists() or SUMMARY.exists():
        raise FileExistsError('Partial run: preserve artifacts; use a new experiment version')
    paths = ['eval/domain_probe_training.json', 'eval/domain_breadth_training.json',
             'eval/domain_breadth_questions.json', 'eval/grey_domain.local.json',
             'config/grey_domain_v1.json', 'data/index/multilingual_e5_curated.json',
             'src/librarian/evaluate_domain_breadth.py', 'src/librarian/search.py',
             'src/librarian/rerank.py', 'src/librarian/evidence_gate.py',
             'src/librarian/domain_guard.py', 'src/librarian/heading_context.py',
             'src/librarian/metric_choice.py', 'src/librarian/ranking_fusion.py']
    fingerprint = lambda: {p: digest(ROOT / p) for p in paths}
    hashes = fingerprint()
    historical = json.loads((ROOT / paths[0]).read_text(encoding='utf-8'))['questions']
    extra = json.loads((ROOT / paths[1]).read_text(encoding='utf-8'))
    training = historical + [dict(query=q, in_domain=label) for key, label in [('positive', True), ('negative', False)] for q in extra[key]]
    spec = json.loads((ROOT / paths[2]).read_text(encoding='utf-8'))
    fresh = [{**r, 'split': 'fresh_full_search'} for r in spec['questions']]
    prior = json.loads((ROOT / paths[3]).read_text(encoding='utf-8'))['rows']
    known = [{**r, 'split': 'known_fixed_result_replay'} for r in prior if r['split'] != 'fixed_result_policy_replay']
    requests = fresh + known
    normalized = lambda q: ' '.join(q.split()).casefold()
    train_text = [normalized(r['query']) for r in training]
    if len(set(train_text)) != len(train_text):
        raise ValueError('Duplicate training query')
    if set(train_text) & {normalized(r['query']) for r in fresh}:
        raise ValueError('Train/evaluation exact query overlap')
    index = E5SearchIndex.load()
    encode = lambda rows: index.model.encode(['query: '+' '.join(r['query'].split()) for r in rows], normalize_embeddings=True, convert_to_numpy=True)
    x = encode(training)
    y = np.asarray([r['in_domain'] for r in training])
    model = LogisticRegression(C=spec['model']['C'], class_weight=spec['model']['class_weight'], random_state=spec['model']['seed']).fit(x, y)
    vectors = encode(requests)
    scores = model.predict_proba(vectors)[:, 1]
    old = load_guard()
    rows = []
    for request, vector, score in zip(requests, vectors, scores):
        results = request['results'] if request['split'] == 'known_fixed_result_replay' else index.search(request['query'], mode='rerank')
        if any(r['retrieval_mode'] != 'rerank' for r in results):
            raise RuntimeError('Unexpected E5 fallback')
        before = assess_evidence(results, request['query'])
        after = candidate_decision(results, request['query'], float(score))
        rows.append({**{k: request[k] for k in ['id','query','kind','split']}, 'training_query': normalized(request['query']) in set(train_text), 'domain_v1': old.signal(vector, request['query'], ENCODER_REVISION)['score'],
                     'domain_v2': float(score), 'before': before, 'after': after, 'results': results})
        print(request['id'], before['status'], '->', after['status'], round(float(score), 3), flush=True)
    new = rows[:len(fresh)]
    checks = {
        'fresh_valid_new_rejections': [r['id'] for r in new if r['kind']=='course' and r['before']['status']!='no_support' and r['after']['status']=='no_support'],
        'fresh_absent_improved': [r['id'] for r in new if r['kind']=='absent' and r['before']['status']!='no_support' and r['after']['status']=='no_support'],
        'fresh_absent_supported_remaining': [r['id'] for r in new if r['kind']=='absent' and r['after']['status']=='supported'],
        'known_pancake_rejected': next(r for r in rows if r['id']=='gd14')['after']['status']=='no_support',
        'fresh_valid_still_no_support': [r['id'] for r in new if r['kind']=='course' and r['after']['status']=='no_support'],
        'fresh_domain_misclassifications_at_half': [r['id'] for r in new if (r['domain_v2']>=.5)!=(r['kind']=='course')],
        'known_valid_new_rejections': [r['id'] for r in rows[len(fresh):] if r['kind']=='course' and r['before']['status']!='no_support' and r['after']['status']=='no_support']}
    checks['predeclared_criteria_met'] = (not checks['fresh_valid_new_rejections'] and len(checks['fresh_absent_improved']) >= 2 and not checks['fresh_absent_supported_remaining'] and checks['known_pancake_rejected'])
    if hashes != fingerprint():
        raise RuntimeError('Inputs changed during evaluation')
    artifact = {'version':'domain-breadth-v2-experimental', 'encoder_id':MODEL_ID, 'encoder_revision':ENCODER_REVISION,
                'training_count':len(training), 'training_hashes':{p:hashes[p] for p in paths[:2]},
                'hyperparameters':spec['model'], 'sklearn_version':sklearn.__version__,
                'coefficients':model.coef_[0].tolist(), 'intercept':float(model.intercept_[0])}
    data = {'created_at':datetime.now(timezone.utc).isoformat(), 'hashes':hashes, 'checks':checks, 'rows':rows}
    MODEL.write_text(json.dumps(artifact, indent=2)+'\n', encoding='utf-8')
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    SUMMARY.write_text(json.dumps({'version':spec['version'], 'created_at':data['created_at'], 'hashes':hashes,
        'raw_sha256':digest(OUTPUT), 'model_sha256':digest(MODEL), 'training_count':len(training),
        'fresh_full_search_count':len(fresh), 'known_fixed_result_replay_count':len(known),
        'production_changed':False, 'broad_release_accepted':False, 'checks':checks}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    render(data)
    print(json.dumps(checks, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
