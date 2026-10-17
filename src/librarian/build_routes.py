from __future__ import annotations
import ast, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'data/snapshot/course-2026-10-17-v1/app.py'
OUT=ROOT/'config/streamlit_routes.json'

def literal(node, key, default=None):
    for kw in node.keywords:
        if kw.arg==key and isinstance(kw.value,ast.Constant):return kw.value.value
    return default

def slug(s):
    s=s.lower().strip()
    s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s

tree=ast.parse(APP.read_text(encoding='utf-8-sig'))
rows=[]
for node in ast.walk(tree):
    if not isinstance(node,ast.Call):continue
    try: fn=ast.unparse(node.func)
    except Exception: continue
    if fn!='st.Page' or not node.args or not isinstance(node.args[0],ast.Constant):continue
    path=str(node.args[0].value).replace('\\','/')
    title=literal(node,'title')
    explicit=literal(node,'url_path')
    candidate=explicit or (slug(title) if title else Path(path).stem)
    rows.append({'source_path':path,'title':title,'url_path':candidate,'route_origin':'explicit' if explicit else 'derived_candidate','line':node.lineno})
rows.sort(key=lambda x:x['source_path'])
OUT.write_text(json.dumps({'source_app':'app.py','streamlit_base_url':None,'route_count':len(rows),'routes':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Parsed {len(rows)} Streamlit routes; {sum(r["route_origin"]=="explicit" for r in rows)} explicit, {sum(r["route_origin"]!="explicit" for r in rows)} derived candidates.')
print('Examples:',json.dumps(rows[:4],ensure_ascii=False))
