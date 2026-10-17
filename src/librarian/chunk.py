from __future__ import annotations
import json, re, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
INPUT=ROOT/'data/normalized/documents.jsonl'
OUTPUT=ROOT/'data/normalized/chunks.jsonl'
REPORT=ROOT/'data/normalized/chunk_report.json'
MAX_CHARS=1100
OVERLAP=140

def provenance(path, kind):
    p=path.lower()
    if p.startswith('resources/'):
        return 'course_original'
    if p.endswith('.md') and '/theory/' in p:
        return 'course_summary_or_extension'
    if p.startswith('views/'):
        return 'streamlit_presentation_text'
    if '.ipynb' in p:
        return 'course_notebook_or_solution'
    if 'syllabus' in p or p=='readme.md':
        return 'project_documentation'
    return 'unknown'

def split_text(text, cap=MAX_CHARS):
    text=text.strip()
    if len(text)<=cap:return [text] if text else []
    # Keep heading/paragraph boundaries when possible; split long paragraphs only as fallback.
    paras=re.split(r'\n\s*\n',text)
    out=[]; current=''
    for para in paras:
        para=para.strip()
        if not para: continue
        if len(para)>cap:
            if current: out.append(current); current=''
            start=0
            while start<len(para):
                end=min(len(para),start+cap)
                if end<len(para):
                    cut=max(para.rfind(' ',start,end),para.rfind('\n',start,end))
                    if cut>start+cap//2:end=cut
                out.append(para[start:end].strip())
                if end>=len(para):break
                start=max(start+1,end-OVERLAP)
            continue
        if len(current)+len(para)+2<=cap: current=(current+'\n\n'+para).strip()
        else:
            if current:out.append(current)
            current=para
    if current:out.append(current)
    return out

records=[]
for line in INPUT.open(encoding='utf-8'):
    doc=json.loads(line)
    for i,text in enumerate(split_text(doc['text'])):
        raw=f"{doc['id']}:{i}:{text}".encode()
        records.append({"chunk_id":hashlib.sha256(raw).hexdigest()[:20],"document_id":doc['id'],"source_path":doc['source_path'],"locator":doc['locator'],"source_kind":doc['source_kind'],"language":doc['language'],"provenance":provenance(doc['source_path'],doc['source_kind']),"streamlit_route":None,"route_status":"unmapped","text":text})
with OUTPUT.open('w',encoding='utf-8',newline='\n') as f:
    for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
report={"snapshot":"course-2026-10-17-v1","chunks":len(records),"max_chars":MAX_CHARS,"overlap_chars":OVERLAP,"by_provenance":{},"by_language_heuristic":{},"by_kind":{},"route_mapping":"pending"}
for r in records:
    for key,field in [('by_provenance','provenance'),('by_language_heuristic','language'),('by_kind','source_kind')]:
        report[key][r[field]]=report[key].get(r[field],0)+1
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
