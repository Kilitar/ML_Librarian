"""Fixed paired test of comparison candidate expansion and coverage selection."""
import hashlib
import html
import json
from pathlib import Path
from search import E5SearchIndex, MANIFEST
from evidence_gate import assess_evidence

ROOT = Path(__file__).resolve().parents[2]
FILES = ('search.py','rerank.py','comparisons.py','semantic_layer.py','domain_concepts.json','constraints.py','diversify.py','evidence_gate.py','concepts.py','acronyms.py','hybrid.py','chunk_text.py','snippet_format.py')


def hashes():
    return {n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in FILES}


def main():
    path = ROOT / 'eval/contextual_questions.json'
    question_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    source_hashes = hashes()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    questions = json.loads(path.read_text(encoding='utf-8'))['questions']
    index = E5SearchIndex.load()
    rows = []
    for question in questions:
        row = dict(question)
        for variant, enabled in (('before',False),('after',True)):
            results = index.search(question['query'],mode='rerank',comparison_tuning=True,comparison_experiment=enabled,comparison_strategy='contextual' if enabled else 'coverage')
            if any(r['retrieval_mode'] != 'rerank' for r in results):
                raise RuntimeError('Unexpected fallback')
            row[variant] = {'results':results,'decision':assess_evidence(results,question['query'])}
        rows.append(row)
        print(question['id'],row['before']['results'][0]['chunk_id'],'->',row['after']['results'][0]['chunk_id'],flush=True)
    if (hashlib.sha256(path.read_bytes()).hexdigest() != question_hash or hashes() != source_hashes
            or manifest != json.loads(MANIFEST.read_text(encoding='utf-8'))):
        raise ValueError('Evaluation inputs changed')
    output = {'questions_sha256':question_hash, 'index_manifest':manifest,
              'source_hashes':source_hashes,
              'scope':'Six development, three new wordings of known topics, three regression questions. Before is current production; after is contextual experiment. Codex provisional review, not independent validation.', 'rows':rows}
    (ROOT/'eval/contextual_comparison.local.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    parts = ['<!doctype html><meta charset="utf-8"><title>Srovnávací dotazy před/po</title><style>body{font:16px system-ui;background:#111827;color:#eee;margin:30px}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}pre{white-space:pre-wrap;background:#1f2937;padding:15px}</style><h1>Srovnávací dotazy – společná porovnávací osa</h1><p>Stejný index/model. Rozklad dotazu doplňuje kandidáty pro obě části; skóre původní celé otázky zůstává oddělené. Nejde o ověření faktické správnosti ani o fine-tuning vah.</p>']
    for row in rows:
        parts.append('<h2>'+html.escape(row['id']+' · '+row['query'])+'</h2><main>')
        for variant in ('before','after'):
            parts.append('<section><h3>'+variant+'</h3><p>'+html.escape(str(row[variant]['decision']))+'</p>')
            for rank,p in enumerate(row[variant]['results'],1):
                parts.append('<details'+(' open' if rank<=2 else '')+'><summary>'+str(rank)+'. '+html.escape(p['source_path'])+'</summary><p>'+html.escape(str(p['comparison_aspects']))+' '+html.escape(str(p['aspect_scores']))+'</p><pre>'+html.escape(p['text'])+'</pre></details>')
            parts.append('</section>')
        parts.append('</main>')
    (ROOT/'eval/contextual_comparison.local.html').write_text('\n'.join(parts),encoding='utf-8')


if __name__ == '__main__':
    main()
