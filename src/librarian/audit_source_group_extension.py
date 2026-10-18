"""Audit source-informed contrast pairs; never retrieve, score, fit or select thresholds."""
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

from calibration_data import coverage, group_pairs, query_key

ROOT = Path(__file__).resolve().parents[2]


def main():
    paths = ['eval/source_group_extension_notes.json',
             'data/normalized/chunks_curated.jsonl',
             'eval/calibration_collection_labeled.local.json',
             'eval/calibration_reserved_test_questions.json',
             'config/calibration_protocol.json',
             'src/librarian/audit_source_group_extension.py',
             'src/librarian/calibration_data.py']
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    read = lambda p: json.loads((ROOT/p).read_text(encoding='utf-8'))
    notes = read(paths[0])
    assert notes['corpus_sha256'] == hashes[paths[1]]
    assert hashes[paths[2]] == read('eval/calibration_collection_labeled_summary.json')['raw_sha256']
    old = read(paths[2])['rows']
    forbidden_queries = {query_key(r['query']) for r in old}
    forbidden_queries.update(query_key(q['query']) for q in read(paths[3])['questions'])
    chunks = {c['chunk_id']: c for c in map(json.loads, (ROOT/paths[1]).read_text(encoding='utf-8').splitlines())}
    new = []
    for note in notes['pairs']:
        c = chunks[note['chunk_id']]
        assert note['source_path'] == c['source_path'] and note['locator'] == c['locator']
        assert note['text_sha256'] == hashlib.sha256(c['text'].encode()).hexdigest()
        assert query_key(note['query']) not in forbidden_queries
        forbidden_queries.add(query_key(note['query']))
        assert note['label'] in ('direct', 'partial', 'topic_only', 'irrelevant', 'unjudgeable')
        assert note['reason'].strip()
        new.append({**note, 'text': c['text'], 'input': c['text'],
            'study': 'source_group_extension', 'fitted_versions': [],
            'target': 1 if note['label']=='direct' else 0 if note['label'] in ('topic_only','irrelevant') else None,
            'review_status': 'codex_provisional', 'all_known_inspected': True})
    grouped = group_pairs(old+new)
    fresh = [r for r in grouped if r['study']=='source_group_extension']
    old_components = {r['component'] for r in grouped if r['study']!='source_group_extension'}
    # Reject an accidental query/source/text bridge, including corpus text copies.
    assert not old_components.intersection(r['component'] for r in fresh)
    assert not any(r['component_fitted_versions'] for r in fresh)
    minimums = read(paths[4])['minimums']
    summary = dict(input_hashes=hashes, scope=notes['scope'],
        new_pairs=len(fresh), new_passages=len({r['chunk_id'] for r in fresh}),
        new_source_groups=len({r['component'] for r in fresh}),
        labels=dict(Counter(r['label'] for r in fresh)),
        languages=dict(Counter(r['language'] for r in fresh)),
        combined_pairs=len(grouped), combined_components=len({r['component'] for r in grouped}),
        combined_base_development=coverage(grouped, minimums),
        strict_v1_v2_source_transfer=coverage([r for r in grouped if not r['component_fitted_versions']], minimums),
        production_changed=False, model_inference=False, training=False,
        threshold_selected=None, reserved_test_executed=0,
        assignments='All inspected development only. No new train/calibration/test split or release acceptance.')
    artifact = dict(summary=summary, rows=grouped)
    raw = ROOT/'eval/source_group_extension.local.json'
    if raw.exists():
        assert json.loads(raw.read_text(encoding='utf-8')) == artifact, 'Frozen extension changed; use new version'
    else:
        raw.write_text(json.dumps(artifact, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    summary['raw_sha256'] = hashlib.sha256(raw.read_bytes()).hexdigest()
    (ROOT/'eval/source_group_extension_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    esc = lambda v: html.escape(str(v))
    page = ['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nové zdrojové kontrasty</title>',
        '<style>body{font:16px/1.6 system-ui;background:#111827;color:#e5e7eb;max-width:1150px;margin:30px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}a{color:#93c5fd}</style>',
        '<h1>9 oddělených zdrojů · 27 kontrastních párů</h1>',
        '<p>Codex sestavil otázky po přečtení pasáží: nejde o výsledky vyhledávání ani nezávislou přejímku. Každá pasáž má jednu přímou otázku a dvě tematicky blízké otázky bez odpovědi. Opakovaná pasáž není nový nezávislý vzorek. Štítky hodnotí pokrytí, nikoli faktickou správnost zdroje. Produkce se nemění.</p>',
        '<p><a href="/eval/calibration_collection_labeled_review.local.html">Předchozích120 výsledků</a></p>',
        '<details><summary>Úplný audit</summary><pre>'+esc(json.dumps(summary, ensure_ascii=False, indent=2))+'</pre></details>']
    for cid in dict.fromkeys(r['chunk_id'] for r in fresh):
        rows = [r for r in fresh if r['chunk_id']==cid]
        page.append('<section><h2>'+esc(rows[0]['source_path'])+'</h2><p>'+esc(cid+' · '+str(rows[0]['locator']))+'</p><pre>'+esc(rows[0]['text'])+'</pre>')
        for r in rows:
            page.append('<article><h3>'+esc(r['id']+' · '+r['label'])+'</h3><blockquote>'+esc(r['query'])+'</blockquote><p>'+esc(r['reason'])+'</p></article>')
        page.append('</section>')
    (ROOT/'eval/source_group_extension_review.local.html').write_text('\n'.join(page), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
