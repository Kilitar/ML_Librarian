"""Frozen paired experiment; reranker predictions shared between both arms."""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from search import E5SearchIndex, MANIFEST
from rerank import PassageReranker
from evidence_gate import assess_evidence

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'eval/ranking_fusion_v2.local.json'
REPORT = ROOT / 'eval/ranking_fusion_v2_review.local.html'


class SharedPredictions:
    def __init__(self):
        self.model = PassageReranker()
        self.cache = {}

    def score_details(self, query, documents, **kwargs):
        key = (query, tuple(d['chunk_id'] for d in documents), repr(kwargs))
        if key not in self.cache:
            self.cache[key] = self.model.score_details(query, documents, **kwargs)
        return self.cache[key]


def render(data):
    esc = lambda s: html.escape(str(s))
    page = ['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Weak rank fusion</title>',
            '<style>body{font:16px/1.5 system-ui;max-width:1450px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}.columns{display:grid;grid-template-columns:1fr 1fr;gap:20px}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary,button{cursor:pointer}a{color:#93c5fd}@media(max-width:800px){.columns{grid-template-columns:1fr}}</style>',
            '<h1>Slabé výsledky: reranker vs. spojení pořadí</h1>',
            '<p>Stejné otázky, kandidáti a skutečné predikce modelu. Vpravo jen při max whole-query všech kandidátů &lt; .10: rovné RRF hlasy surového E5 a rerankeru, k=60, bez bonusů za zdroj. Speciální sémantické plány/srovnání/zkratky beze změny. Skóre opory se nepřepočítává. Zlepšené pořadí samo nepotvrzuje odpověď.</p>',
            '<p>Varianta v1 s hranicí .20 byla odmítnuta: změnila nejistou českou PCA otázku na bez opory. V2 hranicí .10 zachovává stav opory. Všechny otázky jsou nyní vývojové (včetně původně nových formulací); nejde o nezávislou přejímku. Každý úryvek lze rozbalit.</p>',
            '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>']
    for row in data['rows']:
        page.append(f"<section id='{esc(row['id'])}'><h2>{esc(row['id'])}</h2><blockquote>{esc(row['query'])}</blockquote><button onclick=\"navigator.clipboard.writeText(this.parentElement.querySelector('blockquote').innerText)\">Kopírovat dotaz</button><p>{esc(row['split'])}</p><div class='columns'>")
        for key, title in [('before','Původní řazení'),('after','Slabá fúze pořadí')]:
            page.append(f"<div><h3>{title} · {esc(row[key+'_decision']['status'])}</h3>")
            for n, r in enumerate(row[key],1):
                page.append(f"<article><details><summary>{n}. {esc(r['source_path'])}</summary><p>{esc(r['chunk_id'])} · {esc(r.get('locator'))}</p><p>{esc(r['ranking_policy'])} · whole-query {r['whole_query_score']:.4f} · E5 {r['score']:.4f}</p><pre>{esc(r['text'])}</pre></details></article>")
            page.append('</div>')
        page.append('</div></section>')
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if OUTPUT.exists():
        render(json.loads(OUTPUT.read_text(encoding='utf-8')))
        print('Frozen paired results preserved; report regenerated.')
        return
    files = ['eval/acceptance_v1_questions.json','eval/support_repair_questions.json','eval/ranking_fresh_questions.json',
             'src/librarian/search.py','src/librarian/ranking_fusion.py','src/librarian/rerank.py',
             'src/librarian/evidence_gate.py','src/librarian/compare_ranking_fusion.py']
    fingerprint = lambda: {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    hashes = fingerprint()
    manifest_hash = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    questions = []
    for path, split in [(files[0],'development_acceptance'),(files[1],'development_repair'),(files[2],'fresh_formulation')]:
        questions += [{**q,'split':split} for q in json.loads((ROOT/path).read_text(encoding='utf-8'))['questions']]
    index = E5SearchIndex.load()
    predictor = SharedPredictions()
    index.passage_reranker = predictor
    rows=[]
    for q in questions:
        before=index.search(q['query'],mode='rerank',ranking_strategy='reranker')
        after=index.search(q['query'],mode='rerank',ranking_strategy='weak_fusion')
        if any(r['retrieval_mode']!='rerank' for r in before+after):
            raise RuntimeError('Unexpected fallback')
        b,a=assess_evidence(before,q['query']),assess_evidence(after,q['query'])
        rows.append({**q,'before':before,'after':after,'before_decision':b,'after_decision':a})
        print(q['id'], b['status'],a['status'],[r['chunk_id'] for r in after[:3]],flush=True)
        predictor.cache.clear()
    if hashes!=fingerprint() or manifest_hash!=hashlib.sha256(MANIFEST.read_bytes()).hexdigest():
        raise RuntimeError('Inputs changed during experiment')
    protected=[r for r in rows if r['before_decision']['status']=='supported']
    summary={'supported_queries':len(protected),
             'supported_order_changed':sum([p['chunk_id'] for p in r['before']]!=[p['chunk_id'] for p in r['after']] for r in protected),
             'new_supported_absent':sum(r.get('expected')=='no_support' and r['after_decision']['status']=='supported' for r in rows),
             'gate_status_changed':sum(r['before_decision']['status']!=r['after_decision']['status'] for r in rows),
             'fusion_queries':sum(bool(r['after']) and r['after'][0]['ranking_policy']=='weak-fusion-v2' for r in rows)}
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'manifest_sha256':manifest_hash,'summary':summary,'rows':rows}
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    render(data)
    print(summary,flush=True)


if __name__=='__main__':
    main()
