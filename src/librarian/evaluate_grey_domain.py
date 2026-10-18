"""Frozen grey-band policy experiment: fresh search plus fixed-result replay."""
import hashlib
import html
import json
from datetime import datetime,timezone
from pathlib import Path
from search import E5SearchIndex
from domain_guard import load_guard,ENCODER_REVISION
from evidence_gate import assess_evidence

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'eval/grey_domain.local.json'
REPORT=ROOT/'eval/grey_domain_review.local.html'


def without_signal(results):
    return [{k:v for k,v in r.items() if k!='domain_signal'} for r in results]


def render(data):
    esc=lambda s:html.escape(str(s))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Grey-band domain guard</title>',
          '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary,button{cursor:pointer}a{color:#93c5fd}td,th{padding:8px;border:1px solid #64748b}table{border-collapse:collapse}</style>',
          '<h1>Hraniční opora: podmíněný doménový klasifikátor</h1>',
          '<p>Logistická regrese C=10 balanced, seed0, nad neměněnými E5 embeddingy, naučená z37 historických štítků. Rozhoduje jen v pásmu původního rerankeru [.10,.20), při doménovém skóre &lt;.5. Silné výsledky, základní no_support a strukturální výjimky zachovávají pravidla. Žádný seznam zakázaných slov; žádná změna pořadí ani skóre pasáží.</p>',
          '<p>Doménové skóre není kalibrovanou pravděpodobností správné odpovědi. 24 předem fixovaných nových formulací a4 známé kontroly byly skutečně vyhledány;36 starších výsledků je pouze replay rozhodování. Témata se mohou překrývat s tréninkem; nezávislá lidská přejímka zatím neproběhla.</p>',
          '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>',
          '<h2>Omezený výsledek, přejímka stále neprošla</h2><p>Na nové sadě nezměnil strážce žádný stav; přínos je zde potvrzen jen na známém polském dotazu na polévku. Nový dotaz <b>Jak zrobić naleśniki?</b> zůstává chybně supported (.203), mimo pásmo pojistky. Platná polská otázka na vliv škály gd11 zůstává chybně no_support; doménový model sám nedodává důkaz. Tyto případy nejsou úspěchem.</p>',
          '<h2>Kontrolní kritéria úzké změny</h2><pre>'+esc(json.dumps(data['checks'],ensure_ascii=False,indent=2))+'</pre>',
          '<h2>Historická diagnostika tréninku</h2><p>Samotný klasifikátor v leave-one-out chyboval na PCA a opravě kohoutku. Podmíněné pravidlo zde nezasáhne: PCA má silnou oporu a kohoutek už byl bez opory. Jde o staré fixované výsledky, nikoli současné plné vyhledávání ani nezávislou validaci.</p><table><tr><th>Dotaz</th><th>LOO doménové skóre</th><th>Původní opora</th><th>Podmíněné odmítnutí</th></tr>']
    for r in data['training_diagnostics']:
        if (r['loo_score']>=.5)!=r['in_domain'] or r['conditional_rejection']:
            page.append(f"<tr><td>{esc(r['query'])}</td><td>{r['loo_score']:.3f}</td><td>{esc(r['baseline_status'])} ({r['baseline_whole_score']:.3f})</td><td>{r['conditional_rejection']}</td></tr>")
    page.append('</table><h2>Skutečné výsledky jednotlivých dotazů</h2>')
    for r in data['rows']:
        page.append(f"<section id='{esc(r['id'])}'><h3>{esc(r['id'])}</h3><blockquote>{esc(r['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>{esc(r['split'])} · skupina {esc(r['kind'])}</p><p>Před: <b>{esc(r['before']['status'])}</b> → po: <b>{esc(r['after']['status'])}</b>. Doménové skóre {r['diagnostic_domain_score']:.3f}; skutečný zásah: {r['after'].get('reason')=='out_of_domain_grey_band'}.</p>")
        for n,p in enumerate(r['results'],1):
            page.append(f"<article><details><summary>{n}. {esc(p['source_path'])} · původní whole-query {p['whole_query_score']:.4f}</summary><p>{esc(p['chunk_id'])} · {esc(p.get('locator'))}</p><pre>{esc(p['text'])}</pre></details></article>")
        page.append('</section>')
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if OUTPUT.exists():
        render(json.loads(OUTPUT.read_text(encoding='utf-8')));print('Frozen results preserved.');return
    files=['eval/grey_domain_questions.json','eval/domain_probe_training.json','config/grey_domain_v1.json',
           'src/librarian/domain_guard.py','src/librarian/train_domain_guard.py','src/librarian/evaluate_grey_domain.py',
           'src/librarian/search.py','src/librarian/evidence_gate.py','src/librarian/rerank.py',
           'src/librarian/heading_context.py','src/librarian/metric_choice.py','src/librarian/ranking_fusion.py',
           'data/index/multilingual_e5_curated.json','eval/metric_choice.local.json','eval/grey_domain_training.local.json']
    fingerprint=lambda:{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    hashes=fingerprint();index=E5SearchIndex.load();guard=load_guard()
    frozen=json.loads((ROOT/'eval/metric_choice.local.json').read_text(encoding='utf-8'))['rows']
    replay=[r for r in frozen if r['split']!='historical_fixed_passage_replay']
    questions=json.loads((ROOT/files[0]).read_text(encoding='utf-8'))['questions']
    requests=[{**q,'split':'known_control' if q.get('control') else 'fresh_full_search'} for q in questions]
    requests += [{'id':r['id'],'query':r['query'],'kind':r.get('kind') or ('absent' if r.get('expected')=='no_support' else 'course' if r.get('expected')=='supported' else 'ambiguous'),'split':'fixed_result_policy_replay','results':r['after']} for r in replay]
    vectors=index.model.encode(['query: '+' '.join(r['query'].split()) for r in requests],normalize_embeddings=True,convert_to_numpy=True)
    rows=[]
    for q,vector in zip(requests,vectors):
        diagnostic=guard.signal(vector,q['query'],ENCODER_REVISION)
        if q['split']=='fixed_result_policy_replay':
            results=without_signal(q['results'])
            best=max(p['whole_query_score'] for p in results);first=results[0]
            if .10<=best<.20 and not (first.get('comparison_aspects') or first.get('semantic_plan') or first.get('requested_acronym') or first.get('related_evidence_only')):
                results=[{**r,'domain_signal':diagnostic} for r in results]
        else:
            results=index.search(q['query'],mode='rerank',domain_guard_tuning=True)
        if any(r['retrieval_mode']!='rerank' for r in results):raise RuntimeError('Unexpected fallback')
        before=assess_evidence(without_signal(results),q['query']);after=assess_evidence(results,q['query'])
        rows.append({**{k:v for k,v in q.items() if k!='results'},'diagnostic_domain_score':diagnostic['score'],
                     'before':before,'after':after,'results':results})
        print(q['id'],before['status'],after['status'],round(diagnostic['score'],3),flush=True)
    historical={r['id']:r for r in json.loads((ROOT/'eval/abstention_results.local.json').read_text(encoding='utf-8'))['results']}
    training=[]
    for r in json.loads((ROOT/'eval/grey_domain_training.local.json').read_text(encoding='utf-8'))['rows']:
        base=historical[r['id']];best=max(p['whole_query_score'] for p in base['results'])
        training.append({**r,'baseline_whole_score':best,'baseline_status':base['decision']['status'],
                         'conditional_rejection':.10<=best<.20 and r['loo_score']<.5})
    checks={
        'known_polish_soup_no_support':next(r for r in rows if r['id']=='av11')['after']['status']=='no_support',
        'new_valid_to_no_support':[r['id'] for r in rows if r['kind'] in ('course','answerable') and r['before']['status'] in ('supported','uncertain') and r['after']['status']=='no_support'],
        'supported_status_changes':[r['id'] for r in rows if r['before']['status']=='supported' and r['after']['status']!='supported'],
        'new_supported_absent':[r['id'] for r in rows if r['kind']=='absent' and r['after']['status']=='supported' and r['before']['status']!='supported'],
        'ranking_id_changes':0,
        'historical_loo_new_valid_rejections':[r['id'] for r in training if r['in_domain'] and r['conditional_rejection']]}
    if hashes!=fingerprint():raise RuntimeError('Inputs changed during evaluation')
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'checks':checks,
          'training_diagnostics':training,'rows':rows}
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');render(data)
    print('Checks',checks,flush=True)


if __name__=='__main__':main()
