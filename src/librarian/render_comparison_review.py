"""Render frozen comparison trial, explicit review and production smoke results."""
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    raw_path = ROOT/'eval/comparison_tuning.local.json'
    review = json.loads((ROOT/'eval/comparison_judgments.json').read_text(encoding='utf-8'))
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != review['raw_sha256']:
        raise ValueError('Frozen experiment changed')
    rows = json.loads(raw_path.read_text(encoding='utf-8'))['rows']
    notes = {r['id']:r for r in review['judgments']}
    parts = ['<!doctype html><meta charset="utf-8"><title>Porovnání srovnávacích dotazů</title><style>body{font:16px system-ui;background:#111827;color:#eee;margin:30px}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}pre{white-space:pre-wrap;background:#1f2937;padding:15px}</style><h1>Srovnávací dotazy: experiment a omezené nasazení</h1><p><strong>Obecný experiment zamítnut kvůli regresím. V aplikaci povolena pouze rozpoznaná dvojice supervised / unsupervised learning.</strong></p><p>Prozatímní Codex hodnocení společné opory prvních dvou úryvků, nikoli nezávislá validace ani ověření faktické správnosti. Původních šest ladicích dotazů, tři nově fixované otázky a tři regrese. Níže historické experimentální stavy evidence-v3; produkční kontrola na konci používá evidence-v4 a zobrazuje nejisté dílčí podklady.</p>']
    def passages(results):
        for rank,p in enumerate(results,1):
            parts.append('<details'+(' open' if rank <= 2 else '')+'><summary>'+str(rank)+'. '+html.escape(p['source_path'])+'</summary><pre>'+html.escape(p['text'])+'</pre></details>')
    for row in rows:
        note = notes[row['id']]
        parts.append('<h2>'+html.escape(row['id']+' · '+row['query'])+'</h2><p>'+html.escape(note['reason'])+'</p><main>')
        for v,grade in (('before','first_two_before'),('after','first_two_experiment')):
            for p,j in zip(row[v]['results'][:2],note['passages'][v]):
                if p['chunk_id'] != j['chunk_id'] or hashlib.sha256(p['text'].encode()).hexdigest() != j['text_sha256']:
                    raise ValueError('Stale judgment')
            parts.append('<section><h3>'+v+' · '+note[grade]+'</h3><p>'+html.escape(str(row[v]['decision']))+'</p>')
            passages(row[v]['results'])
            parts.append('</section>')
        parts.append('</main>')
    parts.append('<h1>Skutečná produkční varianta – šest kontrol přes formulář</h1>')
    for row in json.loads((ROOT/'eval/comparison_production.local.json').read_text(encoding='utf-8')):
        parts.append('<h2>'+html.escape(row['query'])+'</h2><p>'+html.escape(str(row['decision']))+'</p>')
        passages(row['results'])
    (ROOT/'eval/comparison_review.local.html').write_text('\n'.join(parts),encoding='utf-8')
    print('Validated frozen passage hashes and rendered comparison_review.local.html')


if __name__ == '__main__':
    main()
