"""Replay presentation grouping over frozen results, with all excerpts visible for audit."""
import hashlib
import html
import json
from pathlib import Path
from result_presentation import partition_results

ROOT=Path(__file__).resolve().parents[2]


def main():
    raw_path=ROOT/'eval/contextual_comparison.local.json'
    rows=json.loads(raw_path.read_text(encoding='utf-8'))['rows']
    parts=['<!doctype html><meta charset="utf-8"><title>Seskupení doprovodných shod</title><style>body{font:16px system-ui;background:#111827;color:#eee;margin:30px}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}pre{white-space:pre-wrap;background:#1f2937;padding:15px}details{margin:12px 0}</style><h1>Hlavní výsledky a další shody</h1><p>Úprava zobrazení, nikoli změna vyhledávání nebo důkaz vyšší přesnosti. Všechny původní pasáže a jejich čísla zůstávají dostupné. Audit známých vývojových případů, bez nezávislé validace.</p>']
    summary=[]
    def passages(numbered):
        for rank,p in numbered:
            parts.append('<details'+(' open' if rank==1 else '')+'><summary>'+str(rank)+'. '+html.escape(p['source_path'])+'</summary><pre>'+html.escape(p['text'])+'</pre></details>')
    for row in rows:
        r=row['after']['results'];status=row['after']['decision']['status']
        main,extra=partition_results(r,status)
        summary.append({'id':row['id'],'main_ranks':[i for i,_ in main],'additional_ranks':[i for i,_ in extra]})
        parts.append('<h2>'+html.escape(row['query'])+'</h2>')
        if not extra:
            parts.append('<p>Beze změny. Stav: '+html.escape(status)+'. U no_support zůstávají všechny slabé shody v aplikaci sbalené.</p>')
            continue
        parts.append('<main><section><h3>Před: všech pět karet</h3>');passages(list(enumerate(r,1)))
        parts.append('</section><section><h3>Po: hlavní karty</h3>');passages(main)
        parts.append('<details><summary>Další shody ('+str(len(extra))+')</summary>');passages(extra)
        parts.append('</details></section></main>')
    output={'scope':'Presentation-only replay over known frozen cases, not relevance accuracy.',
            'raw_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            'policy_sha256':hashlib.sha256(Path(__file__).with_name('result_presentation.py').read_bytes()).hexdigest(),
            'cases':summary,'additional_count':sum(len(r['additional_ranks']) for r in summary)}
    (ROOT/'eval/result_grouping_summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'eval/result_grouping_review.local.html').write_text('\n'.join(parts),encoding='utf-8')
    print('Rendered result_grouping_review.local.html; supplementary passages:',output['additional_count'])


if __name__=='__main__':
    main()
