"""Can an original-model cutoff separate inspected coverage labels? No deployment."""
import hashlib
import html
import json
from pathlib import Path
from datetime import datetime,timezone
import torch
from transformers import AutoModelForSequenceClassification,AutoTokenizer
from calibration_data import select_threshold,query_key

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'eval/base_calibration_diagnostic.local.json'
SUMMARY=ROOT/'eval/base_calibration_diagnostic_summary.json'
REPORT=ROOT/'eval/base_calibration_diagnostic_review.local.html'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


def render(data):
    esc=lambda s:html.escape(str(s))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Proveditelnost kalibrace původního modelu</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}</style>',
        '<h1>Stačí pro původní model jeden práh?</h1><p>Diagnostika na známých vývojových štítcích: původní MiniLM, text+skutečný nadpis, žádné natrénované v1/v2 váhy. Tyto páry nefitovaly tento kandidátní model. Přesný počet vývojových párů je níže; žádný není nový test. Cíl fixován před skórováním: nejméně80% přímých odpovědí a nula chybných přijetí na kalibračních datech. Dílčí opora vynechána. Nejde o kalibraci pravděpodobnosti ani změnu produkce.</p>',
        '<p>Přísný source-disjoint audit je doplňková kontrola přenosu na jiné zdroje. Hlavní použití Librarianu jsou nové otázky nad stejným kurzem. Všechny tyto příklady už byly prohlédnuty; rezervovaný test se nespouští. Ani nalezený vývojový práh by se automaticky nenasadil.</p>',
        '<p><a href="/eval/calibration_data_review.local.html">Audit dat</a> · <a href="/eval/calibration_collection_review.local.html">Nový sběr</a> · <a href="http://localhost:8766/">Librarian</a></p>',
        '<pre>'+esc(json.dumps(data['checks'],ensure_ascii=False,indent=2))+'</pre>']
    for row in data['rows']:
        score='přes limit' if row['score'] is None else f"{row['score']:.4f}"
        page.append(f"<article><h3>{esc(row['id'])} · {esc(row['label'])} · {score}</h3><blockquote>{esc(row['query'])}</blockquote><p>{esc(row['source_path'])} · {esc(row['language'])} · {esc(row['family'])}</p><p>{esc(row['reason'])}</p><pre>{esc(row['input'])}</pre></article>")
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if RAW.exists():
        if sha(RAW)!=read('eval/base_calibration_diagnostic_summary.json')['raw_sha256']:raise ValueError('Frozen diagnostic mismatch')
        render(read('eval/base_calibration_diagnostic.local.json'));print('Frozen diagnostic preserved; rendered only.');return
    if SUMMARY.exists():raise FileExistsError('Preserve partial diagnostic')
    paths=['config/base_pair_calibration_diagnostic.json','eval/calibration_data_audit.local.json',
        'eval/calibration_data_summary.json','eval/calibration_reserved_test_questions.json',
        'src/librarian/diagnose_base_calibration.py','src/librarian/calibration_data.py']
    fingerprint=lambda:{p:sha(ROOT/p) for p in paths};hashes=fingerprint();config=read(paths[0])
    if hashes[paths[1]]!=read(paths[2])['raw_sha256']:raise ValueError('Unbound audit')
    pairs=[r for r in read(paths[1])['rows'] if r['target'] is not None]
    reserved={query_key(q['query']) for q in read(paths[3])['questions']}
    if any(query_key(r['query']) in reserved for r in pairs):raise ValueError('Reserved test query leakage')
    if len({(query_key(p['query']),p['input']) for p in pairs})!=len(pairs):raise ValueError('Duplicate calibration pair')
    torch.set_num_threads(min(8,torch.get_num_threads()))
    options=dict(revision=config['revision'],cache_dir=str(ROOT/'.cache/hf'),local_files_only=True,trust_remote_code=False,token=False)
    tokenizer=AutoTokenizer.from_pretrained(config['base_model'],**options)
    model=AutoModelForSequenceClassification.from_pretrained(config['base_model'],use_safetensors=True,**options).eval()
    encoded=[tokenizer(r['query'],r['input'],truncation=False) for r in pairs];scores=[None]*len(pairs)
    with torch.inference_mode():
        for start in range(0,len(pairs),config['batch_size']):
            ids=[n for n in range(start,min(start+config['batch_size'],len(pairs))) if len(encoded[n]['input_ids'])<=config['max_tokens']]
            if not ids:continue
            batch=tokenizer.pad([encoded[n] for n in ids],padding=True,return_tensors='pt')
            values=torch.sigmoid(model(**batch).logits.reshape(-1)).tolist()
            for n,s in zip(ids,values):scores[n]=s
    rows=[{**r,'score':s,'tokens':len(e['input_ids'])} for r,s,e in zip(pairs,scores,encoded)]
    # Other-variant fit provenance stays in raw rows. This selector sees only
    # original-model fit provenance, which is empty: no fine-tuned state is loaded.
    calibration=[{'role':'calibration','target':r['target'],'score':r['score'],
        'fitted_versions':[],'component_fitted_versions':[]} for r in rows if r['score'] is not None]
    result=select_threshold(calibration,min_recall=config['targets']['min_direct_recall'],max_fpr=config['targets']['max_empirical_false_positive_rate'])
    pos=[r for r in rows if r['target']==1 and r['score'] is not None];neg=[r for r in rows if r['target']==0 and r['score'] is not None]
    lowest=min(pos,key=lambda r:r['score']);highest=max(neg,key=lambda r:r['score'])
    max_recall_zero_fp=sum(r['score']>highest['score'] for r in pos)/len(pos)
    checks={'binary_development_pairs':len(rows),'direct_count':len(pos),'negative_count':len(neg),
        'over_budget':[r['id'] for r in rows if r['score'] is None],
        'selection':result,'max_direct_recall_with_zero_empirical_fp':max_recall_zero_fp,
        'lowest_positive':{'id':lowest['id'],'score':lowest['score']},
        'highest_negative':{'id':highest['id'],'score':highest['score']},
        'operational_threshold':None,'reserved_test_executed':0,'production_changed':False,'broad_release_accepted':False}
    if hashes!=fingerprint():raise ValueError('Inputs changed during diagnostic')
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'checks':checks,'rows':rows}
    RAW.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUMMARY.write_text(json.dumps({k:data[k] for k in ['created_at','hashes','checks']}|{'raw_sha256':sha(RAW)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render(data);print(json.dumps(checks,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
