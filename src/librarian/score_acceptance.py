"""Check predeclared release criteria without changing retrieval or thresholds."""
import hashlib
import html
import json
from pathlib import Path
from diversify import content_key
from source_viewer import SourceCatalog

ROOT=Path(__file__).resolve().parents[2]


def main():
    question_path=ROOT/'eval/acceptance_v1_questions.json'
    raw_path=ROOT/'eval/acceptance_v1_results.local.json'
    spec=json.loads(question_path.read_text(encoding='utf-8'))
    raw=json.loads(raw_path.read_text(encoding='utf-8'))
    review=json.loads((ROOT/'eval/acceptance_v1_judgments.json').read_text(encoding='utf-8'))
    if hashlib.sha256(question_path.read_bytes()).hexdigest()!=raw['questions_sha256']:
        raise ValueError('Questions/criteria changed after retrieval')
    if hashlib.sha256(raw_path.read_bytes()).hexdigest()!=review['raw_sha256']:
        raise ValueError('Reviewed raw results changed')
    notes={j['id']:j for j in review['judgments']}
    for row in raw['rows']:
        if row['kind']=='answerable':
            for p,j in zip(row['results'][:3],notes[row['id']]['passages']):
                if p['chunk_id']!=j['chunk_id'] or hashlib.sha256(p['text'].encode()).hexdigest()!=j['text_sha256']:
                    raise ValueError('Stale passage judgment')
    catalog=SourceCatalog();verified=[];errors=[]
    for source in sorted({p['source_path'] for row in raw['rows'] for p in row['results']}):
        try:
            catalog.original(source);verified.append(source)
        except (ValueError,OSError) as error:
            errors.append({'source':source,'reason':str(error)})
    answerable=[r for r in raw['rows'] if r['kind']=='answerable']
    counts={'answerable_top1_direct':sum(notes[r['id']]['top1_grade']=='direct' for r in answerable),
            'answerable_top3_coverage':sum(notes[r['id']]['top3_covers_core'] for r in answerable),
            'answerable_count':len(answerable),
            'answerable_hard_rejections':sum(r['decision']['status']=='no_support' for r in answerable),
            'absent_no_support':sum(r['kind']=='absent' and r['decision']['status']=='no_support' for r in raw['rows']),
            'ambiguous_uncertain':sum(r['kind']=='ambiguous' and r['decision']['status']=='uncertain' for r in raw['rows']),
            'fallback':sum(any(p['retrieval_mode']!='rerank' for p in r['results']) for r in raw['rows']),
            'exact_duplicates':sum(len(r['results'])-len({content_key(p['text']) for p in r['results']}) for r in raw['rows']),
            'source_integrity_failures':len(errors)}
    checks={}
    for criterion,expected in spec['criteria'].items():
        if criterion.endswith('_min'):
            checks[criterion]=counts[criterion[:-4]]>=expected
        elif criterion.endswith('_max'):
            checks[criterion]=counts[criterion[:-4]]<=expected
        elif criterion.endswith('_required'):
            checks[criterion]=counts[criterion[:-9]]==expected
        else:
            checks[criterion]=counts[criterion]==expected
    summary={'candidate_status':'technical_criteria_passed_human_review_pending' if all(checks.values()) else 'not_accepted',
             'reviewer':review['reviewer'],'criteria':spec['criteria'],'counts':counts,'checks':checks,
             'verified_original_sources':len(verified),'source_errors':errors,
             'questions_sha256':raw['questions_sha256'],'raw_sha256':review['raw_sha256'],
             'retrieval_source_hashes':raw['source_hashes'],'scope':review['scope']}
    (ROOT/'eval/acceptance_v1_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    parts=['<!doctype html><meta charset="utf-8"><title>Přejímka retrievalu v1</title><style>body{font:16px system-ui;max-width:1200px;margin:30px auto;background:#111827;color:#eee}pre{white-space:pre-wrap;background:#1f2937;padding:15px}details{margin:15px 0}a{color:#93c5fd}</style><h1>Přejímka retrievalu v1</h1><p><strong>Výsledek: '+html.escape(summary['candidate_status'])+'</strong></p><p>Kritéria a otázky byly fixované před během; vyhledávání nebylo laděno. Hodnocení úryvků je prozatímní Codex, lidské posouzení čeká. Nejde o ověření faktické správnosti zdrojů. SHA-256 kontroluje původní soubory, ne pravdivost tvrzení.</p><pre>'+html.escape(json.dumps({'criteria':spec['criteria'],'counts':counts,'checks':checks,'verified_original_sources':len(verified)},ensure_ascii=False,indent=2))+'</pre><p>Blokátory: <a href="#av02">av02 – částečná opora volby metriky</a>, <a href="#av08">av08 – PCA odmítnuto</a>, <a href="#av11">av11 – recept jako nejistý dotaz</a>. K lidské kontrole také <a href="#av01">av01 – rozdílná doporučení metrik</a> a <a href="#av04">av04 – kódování kategorií</a>.</p>']
    for row in raw['rows']:
        parts.append('<h2 id="'+row['id']+'">'+html.escape(row['id']+' · '+row['query'])+'</h2><p>Stav aplikace: '+html.escape(str(row['decision']))+'</p><p>Očekávané pokrytí: '+html.escape(row['coverage'])+'</p>')
        if row['id'] in notes:
            j=notes[row['id']]
            parts.append('<p>První: '+j['top1_grade']+' · pokrytí jádra v prvních třech: '+str(j['top3_covers_core'])+'</p><p>'+html.escape(j['reason'])+'</p>')
        for rank,p in enumerate(row['results'],1):
            parts.append('<details'+(' open' if rank==1 else '')+'><summary>'+str(rank)+'. '+html.escape(p['source_path'])+'</summary><p>'+html.escape(p['chunk_id'])+'</p><pre>'+html.escape(p['text'])+'</pre></details>')
    (ROOT/'eval/acceptance_v1_review.local.html').write_text('\n'.join(parts),encoding='utf-8')
    print(json.dumps({'status':summary['candidate_status'],'counts':counts,'checks':checks,'verified_sources':len(verified)},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
