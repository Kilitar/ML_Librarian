"""Show provisional annotations with actual excerpts, reasons and split status."""
import hashlib
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    raw=ROOT/'eval/supervised_pair_training.local.json'
    manifest=json.loads((ROOT/'eval/pair_coverage_judgments.json').read_text(encoding='utf-8'))
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=manifest['dataset_sha256']:raise ValueError('Label dataset hash mismatch')
    rows=json.loads(raw.read_text(encoding='utf-8'))['pairs']
    reserved=json.loads((ROOT/'eval/supervised_pair_split.json').read_text(encoding='utf-8'))['excluded_training_question_ids']
    esc=lambda s:html.escape(str(s))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pokrytí otázky: štítky a důvody</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}</style>',
        '<h1>Skutečné pokrytí otázky: provizorní anotace</h1>',
        '<p>58 přečtených dvojic:25 direct,13 partial,20 topic_only. Anotoval Codex, nikoli nezávislý člověk. Hodnotíme pokrytí otázky, ne pravdivost zdroje.13 dílčích párů se netrénuje;5 známých kNN/škála párů je rezervovaný audit. Ze zbývajících40 binárních párů může tokenizer vyřadit další přes limit512 tokenů.</p>',
        '<p>14 kladných otázek bylo napsáno podle stejných pasáží jako negativní příklady: dokument ani název algoritmu tedy sám neurčuje štítek. Jsou to trénovací konstrukce, ne nová vyhledání či nezávislé testy. U nových smysluplných aplikací zůstává partial; žádný blacklist potravin.</p>',
        '<p><a href="/eval/supervised_pair_review.local.html">Trénovací experiment a nové kontrolní výsledky</a> · <a href="http://localhost:8766/">Librarian</a></p>']
    for p in rows:
        status='rezervovaný audit' if p['question_id'] in reserved else 'vynecháno: dílčí/nejisté' if p['target'] is None else 'kladný trénovací pár' if p['target'] else 'negativní trénovací pár'
        page.append(f"<article id='{esc(p['id'])}'><h2>{esc(p['id'])} · {esc(p['label'])}</h2><blockquote>{esc(p['query'])}</blockquote><p>{esc(status)} · autorská odvozená otázka: {p['derived']}</p><p>{esc(p['reason'])}</p><p>{esc(p['source_path'])} · {esc(p['chunk_id'])} · {esc(p.get('locator'))}</p><pre>{esc(p['input'])}</pre></article>")
    target=ROOT/'eval/pair_coverage_review.local.html'
    target.write_text('\n'.join(page),encoding='utf-8')
    print('Rendered',len(rows),'provisional annotations:',target)


if __name__=='__main__':main()
