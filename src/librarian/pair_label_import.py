"""Validate explicit manual exports against frozen pairs; never train or auto-approve."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[2]
LABELS={'direct','partial','topic_only','irrelevant','unjudgeable'}


def text_sha(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()


def validate_export(export,source,raw_sha,pool):
    if export.get('version')!='answerability-pair-review-v3':raise ValueError('Context-bound v3 export required; do not silently reinterpret v1/v2')
    if export.get('pool')!=pool or export.get('frozen_raw_sha256')!=raw_sha:raise ValueError('Wrong pool or frozen source')
    expected=[]
    for q in source['rows']:
        for rank,p in enumerate(q['results'],1):
            body=(p['heading_context']['text']+'\n\n' if p.get('heading_context') else '')+p['text']
            expected.append({'key':'pair_'+str(len(expected)),'question_id':q['id'],'query':q['query'],
                'query_sha256':text_sha(q['query']),'chunk_id':p['chunk_id'],'rank':rank,
                'source_path':p['source_path'],'locator':p.get('locator'),
                'text_sha256':text_sha(p['text']),'input_sha256':text_sha(body)})
    incoming=export.get('pairs')
    if not isinstance(incoming,list) or len(incoming)!=len(expected):raise ValueError('Missing/extra pair rows')
    labels=[]
    for record,wanted in zip(incoming,expected):
        if not isinstance(record,dict) or any(record.get(k)!=v for k,v in wanted.items()):raise ValueError('Altered/reordered pair identity or text binding')
        label=record.get('label');note=record.get('note','')
        if label is not None and label not in LABELS:raise ValueError('Unknown label')
        if not isinstance(note,str) or len(note)>1000:raise ValueError('Invalid annotation note')
        labels.append({**wanted,'label':label,'note':note,
            'target':1 if label=='direct' else 0 if label in ('topic_only','irrelevant') else None,
            'review_status':'unreviewed' if label is None else 'manual_export_unverified'})
    return labels


def main():
    parser=argparse.ArgumentParser();parser.add_argument('export_path',type=Path)
    parser.add_argument('--pool',choices=['original','calibration'],default='calibration')
    args=parser.parse_args();prefix='answerability' if args.pool=='original' else 'calibration_collection'
    raw=ROOT/f'eval/{prefix}.local.json';actual=hashlib.sha256(raw.read_bytes()).hexdigest()
    summary=json.loads((ROOT/f'eval/{prefix}_summary.json').read_text(encoding='utf-8'))
    if actual!=summary['raw_sha256']:raise ValueError('Frozen pool hash mismatch')
    labels=validate_export(json.loads(args.export_path.read_text(encoding='utf-8')),
        json.loads(raw.read_text(encoding='utf-8')),actual,args.pool)
    print(json.dumps({'validated_pairs':len(labels),'labels':dict(Counter(str(r['label']) for r in labels)),
        'binary_labeled':sum(r['target'] is not None for r in labels),'trained':False,
        'human_approval_verified':False},ensure_ascii=False))


if __name__=='__main__':main()
