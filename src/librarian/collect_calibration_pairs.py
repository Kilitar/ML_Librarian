"""Collect only explicitly allowlisted calibration queries; reserved test stays unused."""
import hashlib
import html
import json
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from calibration_data import query_key,source_key,passage_key
from search import E5SearchIndex
from evidence_gate import assess_evidence

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'eval/calibration_collection.local.json'
PARTIAL=ROOT/'eval/calibration_collection_partial.local.json'
SUMMARY=ROOT/'eval/calibration_collection_summary.json'
REPORT=ROOT/'eval/calibration_collection_review.local.html'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


def render(data):
    esc=lambda s:html.escape(str(s))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nové páry pro kalibraci</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}summary,button{cursor:pointer}</style>',
        '<h1>Sběr vývojových dat pro kalibraci</h1><p>24 předem zadaných běžných odborných otázek,8 v každém jazyce. Všech5 skutečných produkčních výsledků zůstává zachováno. Toto je NEANOTOVANÝ kalibrační pool, nikoli test kvality nebo důkaz odpověditelnosti. Platná otázka ani vysoké skóre nedávají automatický kladný štítek.</p>',
        '<p>Rezervovaných12 testovacích otázek se neposílá do vyhledávání ani modelu. Výskyt známé otázky, textu nebo zdroje z tréninkově propojených dat je označen, ne skryt. Po anotaci bude nutné znovu vytvořit celé tranzitivní skupiny; označení jednotlivé pasáže samo nestačí.</p>',
        '<p><a href="/eval/calibration_data_review.local.html">Audit dosavadních dat</a> · <a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>',
        '<pre>'+esc(json.dumps(data['checks'],ensure_ascii=False,indent=2))+'</pre>']
    for r in data['rows']:
        page.append(f"<section><h2>{esc(r['id'])} · {esc(r['language'])} · {esc(r['family'])}</h2><blockquote>{esc(r['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>Produkční stav {esc(r['decision']['status'])}; žádný štítek pokrytí dosud nebyl přiřazen.</p>")
        for n,(p,a) in enumerate(zip(r['results'],r['contamination']),1):
            page.append(f"<article><details><summary>{n}. {esc(p['source_path'])} · whole {p['whole_query_score']:.4f} · známý zdroj: {a['source_seen']}</summary><p>{esc(p['chunk_id'])} · {esc(p.get('locator'))}</p><p>Kontrola vazeb: {esc(a)}</p><pre>{esc(p['text'])}</pre></details></article>")
        page.append('</section>')
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if RAW.exists():
        if sha(RAW)!=read('eval/calibration_collection_summary.json')['raw_sha256']:raise ValueError('Frozen collection mismatch')
        render(read('eval/calibration_collection.local.json'));print('Frozen collection preserved; rendered only.');return
    if SUMMARY.exists():raise FileExistsError('Preserve partial output')
    paths=['eval/calibration_collection_questions.json','eval/calibration_reserved_test_questions.json',
        'eval/calibration_data_audit.local.json','eval/calibration_data_summary.json',
        'src/librarian/collect_calibration_pairs.py','src/librarian/calibration_data.py',
        'src/librarian/search.py','src/librarian/rerank.py','src/librarian/evidence_gate.py',
        'src/librarian/domain_guard.py','src/librarian/heading_context.py','src/librarian/metric_choice.py',
        'config/grey_domain_v1.json','eval/domain_probe_training.json',
        'data/index/multilingual_e5_curated.json','data/normalized/chunks_curated.jsonl','data/normalized/documents.jsonl']
    fingerprint=lambda:{p:sha(ROOT/p) for p in paths}
    hashes=fingerprint()
    if hashes[paths[2]]!=read(paths[3])['raw_sha256']:raise ValueError('Unbound prior audit')
    questions=read(paths[0])['questions'];reserved=read(paths[1])['questions']
    if {query_key(q['query']) for q in questions}&{query_key(q['query']) for q in reserved}:raise ValueError('Calibration/test query overlap')
    if len({q['id'] for q in questions})!=len(questions):raise ValueError('Duplicate collection ID')
    known=[r for r in read(paths[2])['rows'] if r['component_fitted_versions']]
    known_queries={query_key(r['query']) for r in known};known_sources={source_key(r['source_path']) for r in known};known_text={passage_key(r['text']) for r in known}
    rows=[]
    if PARTIAL.exists():
        partial=read('eval/calibration_collection_partial.local.json')
        if partial['hashes']!=hashes:raise ValueError('Inputs changed; preserve partial run')
        rows=partial['rows']
        if [r['id'] for r in rows]!=[q['id'] for q in questions[:len(rows)]]:raise ValueError('Invalid resume prefix')
    index=E5SearchIndex.load()
    for q in questions[len(rows):]:
        results=index.search(q['query'],mode='rerank')
        if len(results)!=5 or any(r['retrieval_mode']!='rerank' for r in results):raise RuntimeError('Unexpected fallback/missing result')
        audit=[{'query_seen':query_key(q['query']) in known_queries,'source_seen':source_key(p['source_path']) in known_sources,
                'text_seen':passage_key(p['text']) in known_text} for p in results]
        rows.append({**q,'results':results,'decision':assess_evidence(results,q['query']),
                     'contamination':audit,'coverage_labels':[None]*len(results)})
        if hashes!=fingerprint():raise ValueError('Inputs changed during collection')
        PARTIAL.write_text(json.dumps({'hashes':hashes,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(q['id'],'collected; fit-connected sources',sum(a['source_seen'] for a in audit),flush=True)
    checks={'queries':len(rows),'pairs':sum(len(r['results']) for r in rows),
        'languages':dict(Counter(r['language'] for r in rows)),'families':len({r['family'] for r in rows}),
        'known_source_passages':sum(a['source_seen'] for r in rows for a in r['contamination']),
        'known_text_passages':sum(a['text_seen'] for r in rows for a in r['contamination']),
        'known_query_requests':sum(any(a['query_seen'] for a in r['contamination']) for r in rows),
        'coverage_annotations':0,'reserved_test_queries':len(reserved),'reserved_test_executed':0,
        'threshold_selected':None,'production_changed':False,'broad_release_accepted':False}
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'checks':checks,'rows':rows}
    RAW.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUMMARY.write_text(json.dumps({k:data[k] for k in ['created_at','hashes','checks']}|{'raw_sha256':sha(RAW)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render(data);print(json.dumps(checks,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
