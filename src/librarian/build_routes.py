from __future__ import annotations
import ast, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'data/snapshot/course-2026-10-17-v1/app.py'
OUT=ROOT/'config/streamlit_routes.json'

def literal(node,key,default=None):
    for kw in node.keywords:
        if kw.arg==key and isinstance(kw.value,ast.Constant):return kw.value.value
    return default

def inferred_filename_path(path):
    name=Path(path).stem
    m=re.match(r'^(\d+)[_\- ]*(.*)$',name)
    if m:
        name=m.group(2) or m.group(1)
    # Streamlit's documented file route rule: strip numeric prefix, lowercase identifier.
    return re.sub(r'[ _]+','_',name).lower()

tree=ast.parse(APP.read_text(encoding='utf-8-sig'))
rows=[]
for node in ast.walk(tree):
    if not isinstance(node,ast.Call):continue
    try: fn=ast.unparse(node.func)
    except Exception:continue
    if fn!='st.Page' or not node.args or not isinstance(node.args[0],ast.Constant):continue
    path=str(node.args[0].value).replace('\\','/')
    title=literal(node,'title')
    explicit=literal(node,'url_path')
    default=bool(literal(node,'default',False))
    candidate='' if default else (explicit or inferred_filename_path(path))
    rows.append({'source_path':path,'title':title,'url_path':candidate,'route_origin':'default_root' if default else ('explicit' if explicit else 'filename_inferred_per_streamlit_docs'),'line':node.lineno})
rows.sort(key=lambda x:x['source_path'])
paths=[r['url_path'] for r in rows if r['url_path']]
duplicates=sorted({p for p in paths if paths.count(p)>1})
OUT.write_text(json.dumps({'source_app':'app.py','streamlit_base_url':None,'route_count':len(rows),'duplicate_paths':duplicates,'routes':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Routes={len(rows)} explicit={sum(r["route_origin"]=="explicit" for r in rows)} inferred={sum(r["route_origin"]=="filename_inferred_per_streamlit_docs" for r in rows)} default={sum(r["route_origin"]=="default_root" for r in rows)} duplicate_paths={len(duplicates)}')
