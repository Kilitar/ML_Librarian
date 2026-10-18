"""Freeze fresh production results before passage review; never tune ranking."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from search import E5SearchIndex, MANIFEST
from evidence_gate import assess_evidence

ROOT = Path(__file__).resolve().parents[2]
FILES = ('search.py','semantic_layer.py','domain_concepts.json','concepts.py','acronyms.py',
         'rerank.py','heading_context.py','ranking_fusion.py','metric_choice.py','domain_guard.py','constraints.py','diversify.py','evidence_gate.py','hybrid.py','chunk_text.py','snippet_format.py','comparisons.py','source_filters.py')


def fingerprints():
    hashes={n: hashlib.sha256((ROOT / 'src/librarian' / n).read_bytes()).hexdigest() for n in FILES}
    for n in ('config/grey_domain_v1.json','eval/domain_probe_training.json'):
        hashes[n]=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
    return hashes


def main():
    destination = ROOT / 'eval/acceptance_v1_results.local.json'
    if destination.exists():
        raise FileExistsError('Acceptance v1 results are frozen; preserve them and use a new evaluation set for another run')
    questions = ROOT / 'eval/acceptance_v1_questions.json'
    question_hash = hashlib.sha256(questions.read_bytes()).hexdigest()
    hashes = fingerprints()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    index = E5SearchIndex.load()
    rows = []
    for q in json.loads(questions.read_text(encoding='utf-8'))['questions']:
        results = index.search(q['query'], mode='rerank')
        if any(r['retrieval_mode'] != 'rerank' for r in results):
            raise RuntimeError('Unexpected fallback')
        decision = assess_evidence(results, q['query'])
        rows.append({**q, 'decision': decision, 'results': results})
        print(q['id'], decision['status'], flush=True)
    if (hashes != fingerprints() or question_hash != hashlib.sha256(questions.read_bytes()).hexdigest()
            or manifest != json.loads(MANIFEST.read_text(encoding='utf-8'))):
        raise RuntimeError('Inputs changed during evaluation')
    output = {'created_at': datetime.now(timezone.utc).isoformat(), 'source_hashes': hashes,
              'questions_sha256': question_hash, 'index_manifest': manifest,
              'scope':'Fresh formulations; provisional Codex review follows. Not independent human validation.', 'rows': rows}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
