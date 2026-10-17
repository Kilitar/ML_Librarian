import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
route_data=json.loads((ROOT/'config/streamlit_routes.json').read_text(encoding='utf-8'))
route_by_source={r['source_path']:r for r in route_data['routes']}
chunks_path=ROOT/'data/normalized/chunks.jsonl'
updated=[]; matched=0
for line in chunks_path.open(encoding='utf-8'):
    c=json.loads(line)
    route=route_by_source.get(c['source_path'])
    if route:
        c['streamlit_route']=route['url_path']
        c['streamlit_title']=route['title']
        c['route_origin']=route['route_origin']
        c['route_status']='candidate_path_needs_live_check'
        matched+=1
    updated.append(c)
with chunks_path.open('w',encoding='utf-8',newline='\n') as f:
    for c in updated:f.write(json.dumps(c,ensure_ascii=False)+'\n')
print(f'Attached route metadata to {matched} chunks; live base URL remains unset.')
