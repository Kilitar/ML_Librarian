"""Frozen independent Qwen scoring trial; no production integration."""
import gc
import hashlib
import html
import json
import time
from pathlib import Path
from datetime import datetime, timezone

from answerability import AnswerabilityScorer, CONFIG
from evidence_gate import assess_evidence
from search import E5SearchIndex

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'eval/answerability.local.json'
SUMMARY = ROOT/'eval/answerability_summary.json'
REPORT = ROOT/'eval/answerability_review.local.html'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def decision(results, query, scores, metadata, threshold):
    before = assess_evidence(results, query)
    if before['status'] != 'supported' or any(r.get('comparison_aspects') or r.get('semantic_plan')
            or r.get('requested_acronym') or r.get('related_evidence_only') for r in results):
        return before
    # An incomplete view is not grounds for a new rejection.
    if any(r['truncated'] for r in metadata):
        return before
    if max(scores) < threshold:
        return {**before,'status':'uncertain','reason':'experimental_answerability_gap',
                'answerability_max':max(scores)}
    return before


def render(data):
    esc=lambda value:html.escape(str(value))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nezávislá kontrola odpověditelnosti</title>',
          '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}button,summary{cursor:pointer}</style>',
          '<h1>Samostatný model: pokrývá pasáž požadavek otázky?</h1>',
          '<p>Qwen3-Reranker0.6B, jiný model než produkční MiniLM. Lokální skóre yes/no bez generované odpovědi, nástrojů nebo API. Fixovaná instrukce a práh .10. Pouze experimentální downgrade ordinary supported→uncertain; nikdy upgrade, změna pořadí ani původního skóre. Při zkrácení jakékoli pasáže se downgrade nepoužije. Nízké skóre neprokazuje nesmyslnost otázky.</p>',
          '<p>9 nových formulací skutečně vyhledáno;12 známých smíšených dotazů a4 známé regrese pouze replay uložených pěti pasáží. Témata se překrývají. Žádná nezávislá lidská/faktická přejímka. Produkce zatím nezměněna.</p>',
          '<p><a href="https://huggingface.co/Qwen/Qwen3-Reranker-0.6B">Oficiální model card</a> · <a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>',
          '<h2>Předem fixovaná kritéria</h2><pre>'+esc(json.dumps(data['checks'],ensure_ascii=False,indent=2))+'</pre>',
          '<p>Skóre modelu není kalibrovaná pravděpodobnost správnosti odpovědi; úspěch v této kontrole sám nestačí k celkové přejímce.</p>']
    for row in data['rows']:
        page.append(f"<section id='{esc(row['id'])}'><h2>{esc(row['id'])} · {esc(row['kind'])}</h2><blockquote>{esc(row['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>{esc(row['split'])} · před <b>{esc(row['before']['status'])}</b> → experiment <b>{esc(row['after']['status'])}</b> · skórování {row['seconds']:.2f}s</p>")
        for n,(r,s,m) in enumerate(zip(row['results'],row['scores'],row['metadata']),1):
            page.append(f"<article><details><summary>{n}. {esc(r['source_path'])} · původní whole {r['whole_query_score']:.4f} · nezávislé yes {s:.4f}</summary><p>{esc(r['chunk_id'])} · {esc(r.get('locator'))} · použito {m['used_document_tokens']}/{m['document_tokens']} tokenů</p><pre>{esc(r['text'])}</pre></details></article>")
        page.append('</section>')
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if RAW.exists():
        summary=json.loads(SUMMARY.read_text(encoding='utf-8'))
        if summary['raw_sha256']!=sha(RAW):raise ValueError('Frozen raw hash mismatch')
        render(json.loads(RAW.read_text(encoding='utf-8')))
        print('Frozen results preserved; rendered only.');return
    if SUMMARY.exists():raise FileExistsError('Preserve partial trial; use a new version')
    paths=['config/answerability_experiment.json','eval/answerability_questions.json',
           'eval/mixed_intent.local.json','eval/domain_breadth.local.json','eval/grey_domain.local.json',
           'src/librarian/answerability.py','src/librarian/evaluate_answerability.py',
           'src/librarian/search.py','src/librarian/rerank.py','src/librarian/evidence_gate.py',
           'src/librarian/domain_guard.py','src/librarian/heading_context.py',
           'src/librarian/metric_choice.py','src/librarian/ranking_fusion.py',
           'config/grey_domain_v1.json','eval/domain_probe_training.json',
           'data/index/multilingual_e5_curated.json','data/normalized/chunks_curated.jsonl',
           'data/normalized/documents.jsonl']
    fingerprint=lambda:{p:sha(ROOT/p) for p in paths}
    hashes=fingerprint();config=json.loads(CONFIG.read_text(encoding='utf-8'))
    fresh=json.loads((ROOT/paths[1]).read_text(encoding='utf-8'))['questions']
    # Validate independent model/cache before paying for fresh retrieval.
    start=time.perf_counter();scorer=AnswerabilityScorer();load_seconds=time.perf_counter()-start
    from huggingface_hub import hf_hub_download
    snapshot=Path(hf_hub_download(config['model_id'],'config.json',revision=config['revision'],cache_dir=str(ROOT/'.cache/hf'),local_files_only=True)).parent
    model_hashes={p.name:sha(p) for p in snapshot.iterdir() if p.is_file()}
    requests=[];index=E5SearchIndex.load()
    for q in fresh:
        results=index.search(q['query'],mode='rerank')
        if len(results)!=5 or any(r['retrieval_mode']!='rerank' for r in results):raise RuntimeError('Unexpected fallback/missing results')
        requests.append({**q,'split':'fresh_full_search','results':results})
        print(q['id'],'retrieved',flush=True)
    del index;gc.collect()
    for r in json.loads((ROOT/paths[2]).read_text(encoding='utf-8'))['rows']:
        requests.append({**{k:r[k] for k in ['id','kind','query','results']},'split':'known_fixed_result_replay'})
    prior=json.loads((ROOT/paths[3]).read_text(encoding='utf-8'))['rows']
    prior+=json.loads((ROOT/paths[4]).read_text(encoding='utf-8'))['rows']
    for key in ['db01','db02','db08','gc04']:
        r=next(r for r in prior if r['id']==key)
        requests.append({**{k:r[k] for k in ['id','query','results']},'kind':'meaningful_regression','split':'known_fixed_result_replay'})
    rows=[]
    for q in requests:
        scores,metadata,seconds=scorer.score(q['query'],q['results'])
        before=assess_evidence(q['results'],q['query'])
        after=decision(q['results'],q['query'],scores,metadata,config['reject_below'])
        rows.append({**q,'before':before,'after':after,'scores':scores,'metadata':metadata,'seconds':seconds})
        print(q['id'],before['status'],'->',after['status'],'max',round(max(scores),4),round(seconds,2),'s',flush=True)
    is_downgrade=lambda r:r['before']['status']=='supported' and r['after']['status']!='supported'
    checks={'known_schnitzel_downgraded':is_downgrade(next(r for r in rows if r['id']=='mi01')),
            'fresh_nonsense_supported_remaining':[r['id'] for r in rows if r['split']=='fresh_full_search' and r['kind']=='nonsense' and r['after']['status']=='supported'],
            'fresh_meaningful_supported_downgrades':[r['id'] for r in rows if r['split']=='fresh_full_search' and r['kind']!='nonsense' and is_downgrade(r)],
            'known_meaningful_supported_downgrades':[r['id'] for r in rows if r['split']!='fresh_full_search' and r['kind']!='nonsense' and is_downgrade(r)],
            'max_extra_seconds_per_query':max(r['seconds'] for r in rows),
            'truncated_cases':[r['id'] for r in rows if any(m['truncated'] for m in r['metadata'])]}
    checks['predeclared_criteria_met']=(checks['known_schnitzel_downgraded'] and not checks['fresh_nonsense_supported_remaining']
        and not checks['fresh_meaningful_supported_downgrades'] and not checks['known_meaningful_supported_downgrades']
        and checks['max_extra_seconds_per_query']<=config['promotion_criteria']['max_extra_seconds_per_query'])
    if hashes!=fingerprint():raise RuntimeError('Inputs changed during trial')
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'model_hashes':model_hashes,
          'model_load_seconds':load_seconds,'checks':checks,'rows':rows}
    RAW.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUMMARY.write_text(json.dumps({k:data[k] for k in ['created_at','hashes','model_hashes','model_load_seconds','checks']}|
        {'raw_sha256':sha(RAW),'fresh_full_searches':9,'known_fixed_result_replays':16,
         'production_changed':False,'broad_release_accepted':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render(data);print(json.dumps(checks,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
