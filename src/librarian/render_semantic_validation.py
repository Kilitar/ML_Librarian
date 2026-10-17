"""Render reviewed first passages, checking labels against frozen text hashes."""
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    review = json.loads((ROOT / 'eval/semantic_passage_judgments.json').read_text(encoding='utf-8'))
    datasets = {}
    for name, filename in (('paired', 'semantic_comparison'), ('fresh', 'semantic_fresh_results')):
        path = ROOT / f'eval/{filename}.local.json'
        if hashlib.sha256(path.read_bytes()).hexdigest() != review[f'{name}_raw_sha256']:
            raise ValueError('Frozen result file changed: ' + name)
        datasets[name] = json.loads(path.read_text(encoding='utf-8'))
    judgments = {j['id']: j for j in review['judgments']}
    counts = {key: Counter() for key in ('baseline','layer','fresh_answerable')}
    parts = ['<!doctype html><meta charset="utf-8"><title>Ověření užitečnosti</title><style>body{font:16px system-ui;background:#111827;color:#eee;max-width:1300px;margin:30px auto}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}pre{white-space:pre-wrap;background:#1f2937;padding:15px}details{margin:15px 0}</style><h1>Užitečnost prvního úryvku a nové dotazy</h1><p>Prozatímní hodnocení Codex, nikoli nezávislé lidské hodnocení. Hodnotíme pouze první úryvek; ostatní jsou zobrazeny pro kontrolu. Přímá opora nezaručuje úplnost ani faktickou správnost zdroje. Párová doménová varianta je experiment, ne celý produkční allowlist.</p>']

    def card(row, variant, key):
        results = row[variant]['results'] if variant else row['results']
        decision = row[variant]['decision'] if variant else row['decision']
        j = judgments[key]
        first = results[0]
        if first['chunk_id'] != j['chunk_id'] or hashlib.sha256(first['text'].encode()).hexdigest() != j['text_sha256']:
            raise ValueError('Stale passage judgment: ' + key)
        parts.append('<section><p><strong>'+html.escape(j['grade'])+'</strong> — '+html.escape(j['reason'])+'</p><p>Stav aplikace: '+html.escape(decision['status'])+'</p>')
        for rank, result in enumerate(results, 1):
            parts.append('<details'+(' open' if rank == 1 else '')+'><summary>'+str(rank)+'. '+html.escape(result['source_path'])+'</summary><pre>'+html.escape(result['text'])+'</pre></details>')
        parts.append('</section>')
        return j['grade']

    for i, row in enumerate(datasets['paired']['rows']):
        parts.append('<h2>'+html.escape(row['query'])+'</h2><main>')
        for variant in ('baseline','layer'):
            parts.append('<div><h3>'+('Bez vrstvy' if variant == 'baseline' else 'Experimentální vrstva')+'</h3>')
            grade = card(row, variant, f'paired_{i}_{variant}')
            counts[variant][grade] += 1
            parts.append('</div>')
        parts.append('</main>')
    parts.append('<h1>Nové formulace – nezměněná produkční verze</h1>')
    matched = 0
    for row in datasets['fresh']['rows']:
        parts.append('<h2>'+html.escape(row['id']+' · '+row['query'])+'</h2>')
        grade = card(row, None, row['id'])
        if row['expected'] == 'supported':
            counts['fresh_answerable'][grade] += 1
        matched += row['decision']['status'] == row['expected']
    summary = {'first_passage_grades': {k: dict(v) for k,v in counts.items()},
               'fresh_exact_status_matches': matched, 'fresh_total': len(datasets['fresh']['rows']),
               'scope': review['scope'], 'reviewer':review['reviewer'],
               'fresh_questions_sha256':review['fresh_questions_sha256']}
    parts.insert(1, '<pre>'+html.escape(json.dumps(summary, ensure_ascii=False, indent=2))+'</pre>')
    (ROOT / 'eval/semantic_validation_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (ROOT / 'eval/semantic_validation.local.html').write_text('\n'.join(parts), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
