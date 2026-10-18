"""Frozen real-search diagnostic of mixed intent; never a production verifier."""
import hashlib
import html
import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np

from search import E5SearchIndex
from evidence_gate import assess_evidence

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'eval/mixed_intent.local.json'
SUMMARY = ROOT / 'eval/mixed_intent_summary.json'
REPORT = ROOT / 'eval/mixed_intent_review.local.html'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(data):
    esc = lambda value: html.escape(str(value))
    page = ['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Smíšené otázky: relevance versus odpověditelnost</title>',
            '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}button,summary{cursor:pointer}</style>',
            '<h1>Smíšené otázky: relevance není ověření odpověditelnosti</h1>',
            '<p>12 skutečných vyhledání: známý řízek +11 předem fixovaných dotazů. Čtyři skupiny obsahují nesmysl, odbornou otázku a smysluplné použití ML na potravinových datech. Smysluplnost dotazu neznamená, že jej kurz skutečně zodpovídá. Žádné trénování, seznam jídel ani nová produkční pojistka.</p>',
            '<p>Text-only je původní crossencoder nad samotným úryvkem, bez názvu souboru, titulku a doplněného nadpisu. Není nezávislý model ani ověřovač faktů. Vysoké skóre může přehlédnout nesmyslnou část otázky i bez metadat.</p>',
            '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>',
            '<h2>Výsledek diagnostiky</h2><pre>'+esc(json.dumps(data['checks'], ensure_ascii=False, indent=2))+'</pre>']
    for row in data['rows']:
        page.append(f"<section id='{esc(row['id'])}'><h2>{esc(row['id'])} · {esc(row['kind'])}</h2><blockquote>{esc(row['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>Známá před skórováním: {row['known']} · produkce: <b>{esc(row['decision']['status'])}</b>; max text-only {max(row['text_only_scores']):.4f}</p>")
        for n, (result, score) in enumerate(zip(row['results'], row['text_only_scores']), 1):
            page.append(f"<article><details><summary>{n}. {esc(result['source_path'])} · produkční whole {result['whole_query_score']:.4f} · text-only {score:.4f}</summary><p>{esc(result['chunk_id'])} · {esc(result.get('locator'))}</p><pre>{esc(result['text'])}</pre></details></article>")
        page.append('</section>')
    REPORT.write_text('\n'.join(page), encoding='utf-8')


def main():
    if RAW.exists():
        summary = json.loads(SUMMARY.read_text(encoding='utf-8'))
        if summary['raw_sha256'] != sha(RAW):
            raise ValueError('Frozen raw hash mismatch')
        render(json.loads(RAW.read_text(encoding='utf-8')))
        print('Frozen results preserved; rendered only.')
        return
    if SUMMARY.exists():
        raise FileExistsError('Preserve partial artifacts; use new experiment version')
    paths = ['eval/mixed_intent_questions.json', 'src/librarian/evaluate_mixed_intent.py',
             'src/librarian/search.py', 'src/librarian/rerank.py', 'src/librarian/evidence_gate.py',
             'src/librarian/heading_context.py', 'src/librarian/domain_guard.py',
             'src/librarian/metric_choice.py', 'src/librarian/ranking_fusion.py',
             'config/grey_domain_v1.json', 'eval/domain_probe_training.json',
             'data/index/multilingual_e5_curated.json', 'data/normalized/documents.jsonl',
             'data/normalized/chunks_curated.jsonl']
    fingerprint = lambda: {p: sha(ROOT / p) for p in paths}
    hashes = fingerprint()
    spec = json.loads((ROOT / paths[0]).read_text(encoding='utf-8'))
    index = E5SearchIndex.load()
    rows = []
    for question in spec['questions']:
        results = index.search(question['query'], mode='rerank')
        if len(results) != 5 or any(r['retrieval_mode'] != 'rerank' for r in results):
            raise RuntimeError('Unexpected missing result/fallback')
        scores = np.asarray(index.passage_reranker.model.predict(
            [(question['query'], r['text']) for r in results], batch_size=8,
            show_progress_bar=False, convert_to_numpy=True)).reshape(-1)
        if len(scores) != len(results) or not np.isfinite(scores).all() or np.any((scores<0)|(scores>1)):
            raise ValueError('Invalid text-only scores')
        decision = assess_evidence(results, question['query'])
        rows.append({**question, 'known': question.get('known', False), 'decision': decision,
                     'text_only_scores': scores.astype(float).tolist(), 'results': results})
        print(question['id'], decision['status'], 'text-only max', round(float(scores.max()), 4), flush=True)
    nonsense = [r for r in rows if r['kind'] == 'nonsense']
    checks = {'nonsense_supported_by_production': [r['id'] for r in nonsense if r['decision']['status']=='supported'],
              'nonsense_text_only_at_least_point2': [r['id'] for r in nonsense if max(r['text_only_scores'])>=.2],
              'meaningful_supported_but_text_only_below_point2': [r['id'] for r in rows if r['kind']!='nonsense' and r['decision']['status']=='supported' and max(r['text_only_scores'])<.2],
              'metadata_removal_solves_all_nonsense': all(max(r['text_only_scores'])<.2 for r in nonsense),
              'production_gate_changed': False, 'independent_answerability_verified': False}
    if hashes != fingerprint():
        raise RuntimeError('Inputs changed during experiment')
    data = {'version': spec['version'], 'created_at': datetime.now(timezone.utc).isoformat(),
            'hashes': hashes, 'checks': checks, 'rows': rows}
    RAW.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    SUMMARY.write_text(json.dumps({k: data[k] for k in ['version','created_at','hashes','checks']} |
        {'raw_sha256': sha(RAW), 'full_search_count': len(rows), 'fresh_formulations':11,
         'known_formulations':1, 'broad_release_accepted':False}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    render(data)
    print(json.dumps(checks, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
