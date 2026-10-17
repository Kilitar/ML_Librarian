from __future__ import annotations
import json, re, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'data/normalized/documents.jsonl'
OUT=ROOT/'data/normalized/chunks_curated.jsonl'
REPORT=ROOT/'data/normalized/curation_report.json'
MAX_CHARS=1100; OVERLAP=140
ALLOWED_KINDS={'md','txt','pdf','notebook_markdown'}
ALLOWED_VIEW_CALLS={':st.markdown',':st.write',':st.caption',':st.info',':st.warning',':st.success',':st.error'}
from chunk_text import split_text

records=[]; excluded={}; kept_docs=set()
for line in SOURCE.open(encoding='utf-8'):
    d=json.loads(line); kind=d['source_kind']; keep=kind in ALLOWED_KINDS
    if kind=='streamlit_literal':
        keep=any(d['locator'].endswith(s) for s in ALLOWED_VIEW_CALLS) and len(d['text'])>=80
    if not keep:
        excluded[kind]=excluded.get(kind,0)+1;continue
    texts=split_text(d['text'])
    if not texts:continue
    kept_docs.add(d['source_path'])
    for i,t in enumerate(texts):
        cid=hashlib.sha256(f"{d['id']}:{i}:{t}".encode()).hexdigest()[:20]
        records.append({**{k:d[k] for k in ('id','source_path','locator','source_kind','language')},'chunk_id':cid,'provenance':('course_original' if d['source_path'].startswith('Resources/') else 'streamlit_presentation_text' if d['source_path'].startswith('views/') else 'course_summary_or_exercise'),'streamlit_route':None,'route_status':'unmapped','text':t})
with OUT.open('w',encoding='utf-8',newline='\n') as f:
    for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
routes=json.loads((ROOT/'config/streamlit_routes.json').read_text(encoding='utf-8'))['routes']; by={r['source_path']:r for r in routes}
# attach current route metadata
for r in records:
    meta=by.get(r['source_path'])
    if meta:r['streamlit_route']=meta['url_path'];r['streamlit_title']=meta['title'];r['route_origin']=meta['route_origin'];r['route_status']='candidate_path_needs_live_check'
with OUT.open('w',encoding='utf-8',newline='\n') as f:
    for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
report={'source_records':sum(1 for _ in SOURCE.open(encoding='utf-8')),'curated_chunks':len(records),'unique_sources':len(kept_docs),'excluded_records_by_kind':excluded,'included_kinds':sorted(ALLOWED_KINDS|{'streamlit_markdown_text'}),'chunks_with_route':sum(bool(r.get('streamlit_route')) for r in records)}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
