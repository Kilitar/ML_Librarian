"""Bind provisional coverage notes and regroup development data, without inference."""
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

from calibration_data import coverage, group_pairs
from pair_label_import import text_sha, validate_export

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    paths = ['eval/calibration_collection.local.json',
             'eval/calibration_collection_coverage_notes.json',
             'eval/calibration_data_audit.local.json',
             'eval/calibration_reserved_test_questions.json',
             'config/calibration_protocol.json']
    hashes = {p: sha(p) for p in paths}
    raw_sha = hashes[paths[0]]
    source, notes, old = map(read, paths[:3])
    assert raw_sha == read('eval/calibration_collection_summary.json')['raw_sha256']
    assert notes['frozen_raw_sha256'] == raw_sha
    assert hashes[paths[2]] == read('eval/calibration_data_summary.json')['raw_sha256']
    assert len(notes['pairs']) == sum(len(q['results']) for q in source['rows']) == 120
    export = dict(version='answerability-pair-review-v3', pool='calibration',
                  frozen_raw_sha256=raw_sha, scope=notes['annotator'], pairs=[])
    hydrated = []
    for q in source['rows']:
        for rank, p in enumerate(q['results'], 1):
            n = len(export['pairs'])
            note = notes['pairs'][n]
            assert (note['question_id'], note['rank']) == (q['id'], rank)
            assert note['note'].strip()
            body = (p['heading_context']['text']+'\n\n' if p.get('heading_context') else '')+p['text']
            export['pairs'].append(dict(key=f'pair_{n}', question_id=q['id'], query=q['query'],
                query_sha256=text_sha(q['query']), chunk_id=p['chunk_id'], rank=rank,
                source_path=p['source_path'], locator=p.get('locator'),
                text_sha256=text_sha(p['text']), input_sha256=text_sha(body),
                label=note['label'], note=note['note']))
            hydrated.append(dict(id=f'collection:{q["id"]}_{rank}', query=q['query'],
                input=body, text=p['text'], source_path=p['source_path'],
                language=q['language'], family=q['family'], label=note['label'],
                reason=note['note'], fitted_versions=[], study='collection',
                target=1 if note['label']=='direct' else 0 if note['label'] in ('topic_only','irrelevant') else None,
                all_known_inspected=True, review_status='codex_provisional'))
    bound = validate_export(export, source, raw_sha, 'calibration')
    assert len(bound) == len(hydrated)
    grouped = group_pairs(old['rows']+hydrated)
    fresh = [r for r in grouped if r['study']=='collection']
    clean = [r for r in grouped if not r['component_fitted_versions']]
    floors = read('config/calibration_protocol.json')['minimums']
    summary = dict(input_hashes=hashes, annotator=notes['annotator'],
        labels=dict(Counter(r['label'] for r in fresh)), total_pairs=len(grouped),
        components=len({r['component'] for r in grouped}),
        largest_component=max(Counter(r['component'] for r in grouped).values()),
        new_fit_connected=sum(bool(r['component_fitted_versions']) for r in fresh),
        new_binary=sum(r['target'] is not None for r in fresh),
        new_pool_coverage=coverage(fresh, floors),
        combined_base_development_coverage=coverage(grouped, floors),
        strict_v1_v2_source_transfer_coverage=coverage(clean, floors),
        reserved_test_executions=0, model_inference=False, training=False,
        threshold_selected=None, production_changed=False,
        assignments={'original_base':'inspected development pool; no new fit, not untouched test',
                     'v1_v2':'fit-connected components excluded from source-transfer calibration',
                     'final_test':'12 reserved questions remain unexecuted and unlabeled'})
    # Frozen artifact must remain identical on rerun; this script never searches or scores.
    artifact = dict(summary=summary, export=export, rows=grouped)
    target = ROOT/'eval/calibration_collection_labeled.local.json'
    if target.exists():
        assert json.loads(target.read_text(encoding='utf-8')) == artifact, 'Inputs changed; use a new version'
    else:
        target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    summary['raw_sha256'] = sha('eval/calibration_collection_labeled.local.json')
    (ROOT/'eval/calibration_collection_labeled_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    esc = lambda v: html.escape(str(v))
    page = ['<!doctype html><meta charset="utf-8"><title>Pokrytí kalibračních pasáží</title>',
        '<style>body{font:16px/1.6 system-ui;background:#111827;color:#e5e7eb;max-width:1150px;margin:30px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere}article{border:1px solid #64748b;margin:16px 0;padding:16px}a{color:#93c5fd}</style>',
        '<h1>120 pasáží: provizorní hodnocení pokrytí</h1>',
        '<p>Štítky vytvořil Codex po přečtení celých úryvků. Nejde o nezávislé lidské schválení, faktický audit ani test přesnosti modelu. Partial se nepřevádí na negativní štítek. Produkce a prahy se nemění; 12 rezervovaných otázek zůstává nepoužitých.</p>',
        '<details><summary>Datový audit a vazby</summary><pre>'+esc(json.dumps(summary, ensure_ascii=False, indent=2))+'</pre></details>']
    for q in source['rows']:
        page.append('<h2>'+esc(q['id']+' · '+q['query'])+'</h2>')
        for rank, p in enumerate(q['results'], 1):
            note = next(n for n in notes['pairs'] if n['question_id']==q['id'] and n['rank']==rank)
            page.append('<article><h3>'+esc(f'{rank}. {note["label"]}')+'</h3><p>'+esc(note['note'])+'</p><p>'+esc(p['source_path']+' · '+p['chunk_id'])+'</p>')
            if p.get('heading_context'):
                page.append('<p>'+esc(p['heading_context']['text'])+'</p>')
            page.append('<pre>'+esc(p['text'])+'</pre></article>')
    (ROOT/'eval/calibration_collection_labeled_review.local.html').write_text('\n'.join(page), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
