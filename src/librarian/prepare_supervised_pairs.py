"""Bind provisional manual coverage notes to frozen passages; collect new queries."""
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
from search import E5SearchIndex

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def text_sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def body(p):return (p['heading_context']['text']+'\n\n' if p.get('heading_context') else '')+p['text']


def main():
    notes_path=ROOT/'eval/pair_coverage_notes.json';notes=json.loads(notes_path.read_text(encoding='utf-8'))
    source=ROOT/'eval/answerability.local.json'
    if sha(source)!=notes['frozen_raw_sha256']:raise ValueError('Unbound annotation source')
    source_rows={r['id']:r for r in json.loads(source.read_text(encoding='utf-8'))['rows']}
    output=ROOT/'eval/supervised_pair_training.local.json';manifest=ROOT/'eval/pair_coverage_judgments.json'
    if output.exists():
        m=json.loads(manifest.read_text(encoding='utf-8'))
        if sha(notes_path)!=m['notes_sha256'] or sha(output)!=m['dataset_sha256']:raise ValueError('Frozen labels changed')
    else:
        if manifest.exists():raise FileExistsError('Preserve partial annotation output')
        pairs=[]
        def add(key,query,row,rank,label,reason,derived=False):
            p=row['results'][rank-1]
            if label not in notes['criteria']:raise ValueError('Invalid coverage label')
            pairs.append({'id':key,'query':query,'question_id':row['id'],'derived':derived,
                'rank':rank,'chunk_id':p['chunk_id'],'source_path':p['source_path'],'locator':p.get('locator'),
                'query_sha256':text_sha(query),'text_sha256':text_sha(p['text']),'input_sha256':text_sha(body(p)),
                'label':label,'target':1 if label=='direct' else 0 if label in ('topic_only','irrelevant') else None,
                'reason':reason,'text':p['text'],'input':body(p)})
        for key,rank,label,reason in notes['reviewed']:
            add(key+'_'+str(rank),source_rows[key]['query'],source_rows[key],rank,label,reason)
        for n,(key,rank,query) in enumerate(notes['derived_positive_questions'],1):
            add('derived_'+str(n),query,source_rows[key],rank,'direct','Autorská otázka podle výslovného obsahu stejné pasáže jako negativní pár; ne nový test.',True)
        if len({(p['query_sha256'],p['input_sha256']) for p in pairs})!=len(pairs):raise ValueError('Duplicate pair')
        data={'version':notes['version'],'source_raw_sha256':sha(source),'notes_sha256':sha(notes_path),'pairs':pairs}
        output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        m={k:data[k] for k in ['version','source_raw_sha256','notes_sha256']}
        m.update({'annotator':notes['annotator'],'criteria':notes['criteria'],'dataset_sha256':sha(output),
                  'counts':{k:sum(p['label']==k for p in pairs) for k in notes['criteria']},
                  'pairs':[{k:v for k,v in p.items() if k not in ('input','text')} for p in pairs]})
        manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Bound training labels:',m['counts'],flush=True)
    heldout=ROOT/'eval/supervised_pair_retrieval.local.json'
    if heldout.exists():print('Preserved frozen new retrieval.');return
    paths=['eval/supervised_pair_questions.json','config/supervised_pair_experiment.json',
           'src/librarian/prepare_supervised_pairs.py','src/librarian/search.py','src/librarian/rerank.py',
           'data/index/multilingual_e5_curated.json','data/normalized/chunks_curated.jsonl','data/normalized/documents.jsonl']
    fingerprint=lambda:{p:sha(ROOT/p) for p in paths}
    hashes=fingerprint();index=E5SearchIndex.load();rows=[]
    for q in json.loads((ROOT/paths[0]).read_text(encoding='utf-8'))['questions']:
        r=index.search(q['query'],mode='rerank')
        if len(r)!=5 or any(p['retrieval_mode']!='rerank' for p in r):raise RuntimeError('Unexpected fallback/missing results')
        rows.append({**q,'results':r});print(q['id'],'collected',flush=True)
    if hashes!=fingerprint():raise ValueError('Inputs changed')
    heldout.write_text(json.dumps({'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
