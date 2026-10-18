"""Render a local, manually exportable pair-labeling sheet from frozen evidence."""
import hashlib
import html
import json
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pool',choices=['original','calibration'],default='original')
    pool=parser.parse_args().pool
    prefix='answerability' if pool=='original' else 'calibration_collection'
    raw=ROOT/f'eval/{prefix}.local.json'
    summary=json.loads((ROOT/f'eval/{prefix}_summary.json').read_text(encoding='utf-8'))
    raw_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    if raw_sha!=summary['raw_sha256']:raise ValueError('Frozen raw hash mismatch')
    data=json.loads(raw.read_text(encoding='utf-8'));esc=lambda s:html.escape(str(s))
    pairs=[];page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hodnocení pokrytí otázky</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}label{display:block;margin:8px 0}button{padding:12px;cursor:pointer}a{color:#93c5fd}.toolbar{position:sticky;top:0;background:#111827;padding:12px;border:1px solid #64748b}</style>',
        '<h1>Odpovídá pasáž na celou otázku?</h1><p>Ruční hodnocení konkrétních dvojic, bez předvyplněných štítků. Správné téma samo nestačí. Posuzuj skutečný vztah v otázce; smysluplné použití ML na potravinách není automaticky nesmysl. U složené otázky úplné pokrytí vyžaduje všechny podstatné části.</p>',
        '<p>Hodnocení zůstává pouze v paměti této stránky do exportu. Obnovením stránky se ztratí. Nic se neodesílá do sítě ani do tréninku; exportuješ pouze svůj lokální JSON. Známé otázky jsou vývojová data. Modelová skóre jsou schovaná, aby nesugerovala hodnocení.</p>',
        '<p><a href="/eval/answerability_review.local.html">Modelové srovnání</a> · <a href="http://localhost:8766/">Librarian</a></p>',
        '<div class="toolbar"><span id="progress">0 hodnocení</span> · <button id="export">Exportovat hodnocení JSON</button></div>']
    for row in data['rows']:
        page.append(f"<h2>{esc(row['id'])}</h2><blockquote>{esc(row['query'])}</blockquote><p>{esc(row.get('split','unlabeled_calibration_collection'))}; {esc(row.get('kind',row.get('family','unknown')))}</p>")
        for rank,(result,score) in enumerate(zip(row['results'],row.get('scores',[None]*len(row['results']))),1):
            key=f"pair_{len(pairs)}"
            pairs.append({'key':key,'question_id':row['id'],'query':row['query'],
                'query_sha256':hashlib.sha256(row['query'].encode('utf-8')).hexdigest(),
                'chunk_id':result['chunk_id'],'rank':rank,'source_path':result['source_path'],
                'locator':result.get('locator'),'text_sha256':hashlib.sha256(result['text'].encode('utf-8')).hexdigest(),
                'input_sha256':hashlib.sha256(((result['heading_context']['text']+'\n\n' if result.get('heading_context') else '')+result['text']).encode('utf-8')).hexdigest(),
                'label':None,'note':''})
            page.append(f"<article><h3>{rank}. {esc(result['source_path'])}</h3><p>{esc(result['chunk_id'])} · {esc(result.get('locator'))}</p>")
            if result.get('heading_context'):
                page.append('<p>Nadpis ve zdroji: '+esc(result['heading_context']['text'])+'</p>')
            page.append('<pre>'+esc(result['text'])+'</pre>')
            for value,label in [('direct','Odpovídá na celou otázku'),('partial','Odpovídá jen na část otázky'),('topic_only','Pouze společné téma; požadovaný vztah chybí'),('irrelevant','S otázkou nesouvisí'),('unjudgeable','Nedokážu rozhodnout')]:
                page.append(f'<label><input type="radio" name="{key}" value="{value}"> {label}</label>')
            score_text='' if score is None else f'; Qwen yes {score:.4f}'
            page.append(f'<label>Poznámka <input type="text" data-note="{key}" maxlength="1000"></label><details><summary>Zobrazit modelová skóre</summary>Původní whole {result["whole_query_score"]:.4f}{score_text}</details></article>')
    payload={'version':'answerability-pair-review-v3','pool':pool,'frozen_raw_sha256':raw_sha,
             'scope':'Manual labels, not automatically approved or used for training',
             'labels':{'direct':'Whole-question answer coverage','partial':'Actual partial answer coverage',
                       'topic_only':'Topic match without requested relation',
                       'irrelevant':'Unrelated to question','unjudgeable':'Needs further review'},'pairs':pairs}
    # Never interpolate query/source strings into executable JavaScript.
    safe=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    page.append('<script type="application/json" id="data">'+safe+'</script>')
    page.append('''<script>
const data=JSON.parse(document.getElementById('data').textContent);
const byKey=new Map(data.pairs.map(p=>[p.key,p]));
document.addEventListener('change',e=>{if(e.target.type==='radio'){byKey.get(e.target.name).label=e.target.value;document.getElementById('progress').textContent=data.pairs.filter(p=>p.label!==null).length+' / '+data.pairs.length+' hodnocení';}});
document.addEventListener('input',e=>{if(e.target.dataset.note)byKey.get(e.target.dataset.note).note=e.target.value;});
document.getElementById('export').addEventListener('click',()=>{const out={...data,exported_at:new Date().toISOString()};const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='answerability-pair-labels.local.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
document.getElementById('progress').textContent='0 / '+data.pairs.length+' hodnocení';
</script>''')
    target=ROOT/f'eval/{prefix}_labels.local.html'
    target.write_text('\n'.join(page),encoding='utf-8')
    print('Rendered',len(pairs),'unlabeled frozen pairs:',target)


if __name__=='__main__':main()
