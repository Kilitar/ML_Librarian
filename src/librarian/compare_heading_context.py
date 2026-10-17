"""Paired source-heading experiment; preserve raw output on subsequent runs."""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from search import E5SearchIndex, MANIFEST
from rerank import PassageReranker, parameter_queries
from evidence_gate import assess_evidence

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'eval/heading_context.local.json'
REPORT=ROOT/'eval/heading_context_review.local.html'


class PairedReranker(PassageReranker):
    def __init__(self):
        super().__init__(use_headings=False)
        self.cache={}
        self.enabled=False

    def score_details(self,query,documents,**kwargs):
        key=(query,tuple(d['chunk_id'] for d in documents),repr(kwargs))
        if key not in self.cache:self.cache[key]=super().score_details(query,documents,**kwargs)
        details=self.cache[key]
        if self.enabled and not (kwargs.get('aspects') or kwargs.get('context') or parameter_queries(query)):
            return self.add_heading_context(query,documents,details)
        return details


def render(data):
    esc=lambda x:html.escape(str(x))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Adjacent heading comparison</title>',
          '<style>body{font:16px/1.5 system-ui;max-width:1450px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}.columns{display:grid;grid-template-columns:1fr 1fr;gap:20px}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary,button{cursor:pointer}a{color:#93c5fd}@media(max-width:800px){.columns{grid-template-columns:1fr}}</style>',
          '<h1>Původní úryvek vs. původní přilehlý nadpis</h1><p>Nadpis pouze ze stejného staticky extrahovaného zdroje, bezprostředně před úryvkem (max3 řádky zdrojového kódu). Žádný vygenerovaný text. Slabé skóre původní otázky se ověří také s nadpisem; zachová se vyšší skutečná predikce. Hranice .10/.20 neměníme. Srovnání, parametrové poddotazy a silné pasáže se takto nepřepočítávají.</p>',
          '<p>Vývojová sada, pět předem fixovaných nových formulací a známý nejasný kontrolní dotaz hf06. Prozatímní kontrola, ne nezávislá lidská přejímka ani ověření správnosti zdrojů. Historický replay níže přepočítává jen původních pět pasáží, nikoli celý retrieval.</p>',
          '<a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a>']
    for row in data['rows']:
        page.append(f"<section><h2>{esc(row['id'])}</h2><blockquote>{esc(row['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>{esc(row['split'])}</p><div class='columns'>")
        for arm,title in [('before','Bez přilehlého nadpisu'),('after','S přilehlým nadpisem')]:
            page.append(f"<div><h3>{title} · {esc(row[arm+'_decision']['status'])}</h3>")
            for n,r in enumerate(row[arm],1):
                page.append(f"<article><details><summary>{n}. {esc(r['source_path'])} · relevance {r['whole_query_score']:.4f}</summary><p>{esc(r['chunk_id'])} · {esc(r.get('locator'))}</p>")
                if r.get('heading_context'):
                    h=r['heading_context'];page.append(f"<p>Nadpis: {esc(h['text'])} ({esc(h['locator'])})</p><p>Původní skóre {r['base_whole_query_score']:.4f}; s nadpisem {r['heading_query_score']:.4f}</p>")
                page.append(f"<pre>{esc(r['text'])}</pre></details></article>")
            page.append('</div>')
        page.append('</div></section>')
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if OUTPUT.exists():
        render(json.loads(OUTPUT.read_text(encoding='utf-8')));print('Frozen results preserved.');return
    files=['src/librarian/search.py','src/librarian/rerank.py','src/librarian/heading_context.py',
           'src/librarian/evidence_gate.py','src/librarian/compare_heading_context.py',
           'eval/acceptance_v1_questions.json','eval/support_repair_questions.json',
           'eval/ranking_fresh_questions.json','eval/heading_fresh_questions.json',
           'data/normalized/documents.jsonl','data/index/multilingual_e5_curated.json']
    fingerprint=lambda:{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    hashes=fingerprint();index=E5SearchIndex.load();reranker=PairedReranker();index.passage_reranker=reranker
    questions=[]
    for name in files[5:9]:
        questions += [{**r,'split':'fresh_formulation' if 'heading_fresh' in name else 'development_full_search'} for r in json.loads((ROOT/name).read_text(encoding='utf-8'))['questions']]
    rows=[]
    for q in questions:
        reranker.enabled=False;before=index.search(q['query'],mode='rerank')
        reranker.enabled=True;after=index.search(q['query'],mode='rerank')
        if any(r['retrieval_mode']!='rerank' for r in before+after):raise RuntimeError('Unexpected fallback')
        b,a=assess_evidence(before,q['query']),assess_evidence(after,q['query'])
        rows.append({**q,'before':before,'after':after,'before_decision':b,'after_decision':a})
        print(q['id'],b['status'],a['status'],after[0]['chunk_id'],flush=True);reranker.cache.clear()
    # Broader fixed-passage replay; original availability labels are development.
    lookup={d['chunk_id']:d for d in index.documents}
    historical=json.loads((ROOT/'eval/abstention_results.local.json').read_text(encoding='utf-8'))['results']
    for q in historical:
        before=q['results'];documents=[lookup[r['chunk_id']] for r in before]
        reranker.enabled=False;baseline=reranker.score_details(q['query'],documents)
        reranker.enabled=True;details=reranker.score_details(q['query'],documents)
        after=[]
        for n,r in enumerate(before):
            result={**r,'whole_query_score':float(details['whole_query'][n])}
            if 'base_whole_query' in details:result.update(base_whole_query_score=float(details['base_whole_query'][n]),heading_context=details['heading_contexts'][n],heading_query_score=details['heading_scores'][n])
            after.append(result)
        before=[{**r,'whole_query_score':float(baseline['whole_query'][n])} for n,r in enumerate(before)]
        rows.append({'id':'replay_'+q['id'],'query':q['query'],'expected':q['expected'],'split':'historical_fixed_passage_replay',
                     'before':before,'after':after,'before_decision':assess_evidence(before,q['query']),'after_decision':assess_evidence(after,q['query'])})
        reranker.cache.clear()
    if hashes!=fingerprint():raise RuntimeError('Inputs changed during experiment')
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'rows':rows}
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');render(data)
    print('Completed',len(rows),'rows',flush=True)


if __name__=='__main__':main()
