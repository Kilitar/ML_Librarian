"""Freeze metric-choice coverage and source-formula context comparisons."""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from search import E5SearchIndex
from rerank import PassageReranker, parameter_queries
from heading_context import AdjacentHeadings
from metric_choice import plan
from evidence_gate import assess_evidence

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'eval/metric_choice.local.json'
REPORT=ROOT/'eval/metric_choice_review.local.html'


class PairedReranker(PassageReranker):
    def __init__(self):
        super().__init__(use_headings=False)
        self.catalogs={False:AdjacentHeadings(allow_formula=False),True:AdjacentHeadings()}
        self.enabled=False
        self.cache={}

    def score_details(self,query,documents,**kwargs):
        key=(query,tuple(d['chunk_id'] for d in documents),repr(kwargs))
        if key not in self.cache:self.cache[key]=super().score_details(query,documents,**kwargs)
        details=self.cache[key]
        if not (kwargs.get('aspects') or kwargs.get('context') or parameter_queries(query)):
            self.heading_catalog=self.catalogs[self.enabled]
            return self.add_heading_context(query,documents,details)
        return details


def render(data):
    esc=lambda x:html.escape(str(x))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Metric choice evidence</title>',
          '<style>body{font:16px/1.5 system-ui;max-width:1550px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}.columns{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}article,section{border:1px solid #64748b;padding:14px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary,button{cursor:pointer}a{color:#93c5fd}</style>',
          '<h1>Volba precision / recall: vysvětlení ceny chyb</h1><p>Původní první výsledek zůstává. Pouze u již podpořené otázky s výslovnou prioritou a konkrétním kontextem lze doplnit jednu chybějící pasáž do první trojice. Pomocný dotaz hledá cenu příslušné chyby; jeho skóre NENÍ oporou původní otázky. Nadpis může překlenout jeden samostatný původní st.latex vzorec.</p>',
          '<p>Předem fixované varianty známých metrik plus dříve prohlédnutá vývojová sada. Historický replay níže ověřuje jen pět pevných pasáží, nikoli celý retrieval. Nejde o nezávislou lidskou přejímku ani ověření faktické správnosti zdrojů.</p>',
          '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>']
    for row in data['rows']:
        page.append(f"<section id='{esc(row['id'])}'><h2>{esc(row['id'])}</h2><blockquote>{esc(row['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>{esc(row['split'])} · očekáváno {esc(row.get('expected'))}</p><div class='columns'>")
        arms=[('before','Před změnou')]
        if 'heading_only' in row:arms.append(('heading_only','Jen nadpis přes vzorec'))
        arms.append(('after','Nadpis + doplňující kontext'))
        for arm,title in arms:
            page.append(f"<div><h3>{title} · {esc(row[arm+'_decision']['status'])}</h3>")
            for n,r in enumerate(row[arm],1):
                page.append(f"<article><details><summary>{n}. {esc(r['source_path'])} · původní otázka {r['whole_query_score']:.4f}</summary><p>{esc(r['chunk_id'])} · {esc(r.get('locator'))}</p>")
                if r.get('metric_choice_plan'):
                    m=r['metric_choice_plan'];page.append(f"<p>Pomocný dotaz: {esc(m['facet_query'])}; skóre {esc(r.get('metric_choice_facet_score'))}; doplněná pasáž {esc(r.get('metric_choice_context'))}</p>")
                if r.get('heading_context'):
                    h=r['heading_context'];page.append(f"<p>Nadpis: {esc(h['text'])} ({esc(h['locator'])}); mezilehlý vzorec: {esc(h.get('intervening_formula_locator'))}</p><p>Bez nadpisu {r['base_whole_query_score']:.4f}; s nadpisem {r['heading_query_score']:.4f}</p>")
                page.append(f"<pre>{esc(r['text'])}</pre></details></article>")
            page.append('</div>')
        page.append('</div></section>')
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if OUTPUT.exists():
        render(json.loads(OUTPUT.read_text(encoding='utf-8')));print('Frozen results preserved.');return
    questions=['eval/acceptance_v1_questions.json','eval/support_repair_questions.json','eval/ranking_fresh_questions.json',
               'eval/heading_fresh_questions.json','eval/metric_choice_questions.json']
    files=questions+['src/librarian/search.py','src/librarian/metric_choice.py','src/librarian/heading_context.py',
                    'src/librarian/rerank.py','src/librarian/compare_metric_choice.py','src/librarian/evidence_gate.py',
                    'data/normalized/documents.jsonl','data/index/multilingual_e5_curated.json']
    fingerprint=lambda:{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    hashes=fingerprint();index=E5SearchIndex.load();reranker=PairedReranker();index.passage_reranker=reranker
    requests=[]
    for name in questions:
        requests += [{**q,'split':'fresh_metric_formulation' if name==questions[-1] else 'development_full_search'} for q in json.loads((ROOT/name).read_text(encoding='utf-8'))['questions']]
    rows=[]
    for q in requests:
        reranker.enabled=False;before=index.search(q['query'],mode='rerank',metric_choice_tuning=False)
        reranker.enabled=True
        middle=index.search(q['query'],mode='rerank',metric_choice_tuning=False) if plan(q['query']) else None
        after=index.search(q['query'],mode='rerank',metric_choice_tuning=True)
        if any(r['retrieval_mode']!='rerank' for r in before+after+(middle or [])):raise RuntimeError('Unexpected fallback')
        b,a=assess_evidence(before,q['query']),assess_evidence(after,q['query'])
        row={**q,'before':before,'after':after,'before_decision':b,'after_decision':a}
        if middle is not None:row.update(heading_only=middle,heading_only_decision=assess_evidence(middle,q['query']))
        rows.append(row)
        print(q['id'],b['status'],a['status'],'context',[(r['chunk_id'],r['metric_choice_facet_score']) for r in after if r['metric_choice_context']],flush=True)
        reranker.cache.clear()
    lookup={d['chunk_id']:d for d in index.documents}
    historical=json.loads((ROOT/'eval/abstention_results.local.json').read_text(encoding='utf-8'))['results']
    for q in historical:
        original=q['results'];documents=[lookup[r['chunk_id']] for r in original]
        reranker.enabled=False;before_details=reranker.score_details(q['query'],documents)
        reranker.enabled=True;after_details=reranker.score_details(q['query'],documents)
        row={'id':'replay_'+q['id'],'query':q['query'],'expected':q['expected'],'split':'historical_fixed_passage_replay'}
        for arm,details in [('before',before_details),('after',after_details)]:
            results=[]
            for n,r in enumerate(original):
                result={**r,'whole_query_score':float(details['whole_query'][n])}
                if 'base_whole_query' in details:result.update(base_whole_query_score=float(details['base_whole_query'][n]),heading_context=details['heading_contexts'][n],heading_query_score=details['heading_scores'][n])
                results.append(result)
            row[arm]=results;row[arm+'_decision']=assess_evidence(results,q['query'])
        rows.append(row);reranker.cache.clear()
    if hashes!=fingerprint():raise RuntimeError('Inputs changed during evaluation')
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'rows':rows}
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');render(data)
    print('Completed',len(rows),'rows',flush=True)


if __name__=='__main__':main()
