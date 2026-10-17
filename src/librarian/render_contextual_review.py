"""Validate frozen top-one reviews and show contextual comparison excerpts."""
import hashlib
import html
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]


def main():
    path = ROOT/'eval/contextual_comparison.local.json'
    review = json.loads((ROOT/'eval/contextual_judgments.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != review['raw_sha256']:
        raise ValueError('Frozen raw result changed; new review required')
    rows = json.loads(path.read_text(encoding='utf-8'))['rows']
    notes = {j['id']:j for j in review['judgments']}
    counts = {v:Counter() for v in ('before','after')}
    parts = ['<!doctype html><meta charset="utf-8"><title>Srovnání podle typu výstupu</title><style>body{font:16px system-ui;background:#111827;color:#eee;margin:30px}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}pre{white-space:pre-wrap;background:#1f2937;padding:15px}</style><h1>Regrese vs. klasifikace – porovnávací osa</h1><p>Prozatímní hodnocení Codex. Šest cílových formulací nyní má přímé vysvětlení v prvním úryvku; jsou to varianty stejného známého tématu, nikoli šest nezávislých témat. Tři nové formulace byly fixované před finálním během. Zdrojová fakta nebyla tímto hodnocením ověřena. Druhá a další pasáž mohou stále být slabší.</p>']
    def passages(results):
        for rank,p in enumerate(results,1):
            parts.append('<details'+(' open' if rank<=2 else '')+'><summary>'+str(rank)+'. '+html.escape(p['source_path'])+'</summary><p>Skóre celé otázky: '+str(round(p['whole_query_score'],4))+' · osy: '+str(p.get('context_score'))+'</p><pre>'+html.escape(p['text'])+'</pre></details>')
    for row in rows:
        note = notes[row['id']]
        parts.append('<h2>'+html.escape(row['id']+' · '+row['query'])+'</h2><p>'+html.escape(note['reason'])+'</p><main>')
        for v in ('before','after'):
            first = row[v]['results'][0]; expected=note['first_passages'][v]
            if first['chunk_id'] != expected['chunk_id'] or hashlib.sha256(first['text'].encode()).hexdigest() != expected['text_sha256']:
                raise ValueError('Stale top-one judgment')
            counts[v][note[v+'_grade']]+=1
            parts.append('<section><h3>'+v+' · '+note[v+'_grade']+'</h3><p>'+html.escape(str(row[v]['decision']))+'</p>')
            passages(row[v]['results']); parts.append('</section>')
        parts.append('</main>')
    parts.insert(1,'<pre>'+html.escape(json.dumps({k:dict(v) for k,v in counts.items()},indent=2))+'</pre>')
    parts.append('<h1>Osm skutečných odeslání v produkčním formuláři</h1>')
    for row in json.loads((ROOT/'eval/contextual_production.local.json').read_text(encoding='utf-8')):
        parts.append('<h2>'+html.escape(row['query'])+'</h2><p>'+html.escape(str(row['decision']))+'</p>')
        passages(row['results'])
    (ROOT/'eval/contextual_review.local.html').write_text('\n'.join(parts),encoding='utf-8')
    print('Validated top-one labels and rendered contextual_review.local.html')


if __name__ == '__main__':
    main()
