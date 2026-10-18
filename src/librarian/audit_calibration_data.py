"""Consolidate inspected coverage data and audit calibration leakage, no inference."""
import hashlib
import html
import json
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
from calibration_data import group_pairs,query_key,coverage

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'eval/calibration_data_audit.local.json'
SUMMARY=ROOT/'eval/calibration_data_summary.json'
REPORT=ROOT/'eval/calibration_data_review.local.html'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def body(p):return (p['heading_context']['text']+'\n\n' if p.get('heading_context') else '')+p['text']


def render(data):
    esc=lambda s:html.escape(str(s))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Audit dat pro kalibraci</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article,section{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}summary{cursor:pointer}</style>',
        '<h1>Která data můžeme použít ke kalibraci?</h1>',
        '<p>Sjednocení již prohlédnutých anotací. Žádný nový trénink ani posun prahu. Stejná otázka, soubor nebo doslovná kopie pasáže spojuje celou skupinu; přenos je tranzitivní. Skupina obsahující pár použitý k trénování v1/v2 se nepoužije pro jejich nezávislou kalibraci. Všechny příklady jsou vývojové; žádný není nový netknutý test.</p>',
        '<p>Provizorní štítky Codex hodnotí pokrytí, nikoli pravdivost zdroje. Počet párů není počet nezávislých pozorování. Prahová kalibrace není kalibrace pravděpodobnosti.</p>',
        '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a></p>',
        '<h2>Audit a chybějící pokrytí</h2><pre>'+esc(json.dumps(data['checks'],ensure_ascii=False,indent=2))+'</pre>']
    for c in data['components']:
        page.append('<section><h2>Skupina '+esc(c['id'])+'</h2><pre>'+esc(json.dumps(c,ensure_ascii=False,indent=2))+'</pre></section>')
    for r in data['rows']:
        page.append(f"<article><details><summary>{esc(r['id'])} · {esc(r['label'])} · {esc(r['language'])} · {esc(r['role'])}</summary><blockquote>{esc(r['query'])}</blockquote><p>{esc(r['source_path'])} · skupina {esc(r['component'])}</p><p>{esc(r['reason'])}</p><pre>{esc(r['input'])}</pre></details></article>")
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if RAW.exists():
        if sha(RAW)!=read('eval/calibration_data_summary.json')['raw_sha256']:raise ValueError('Frozen audit hash mismatch')
        render(read('eval/calibration_data_audit.local.json'));print('Frozen audit preserved; rendered only.');return
    if SUMMARY.exists():raise FileExistsError('Preserve partial audit; use a new version')
    paths=['config/calibration_protocol.json','eval/pair_coverage_judgments.json','eval/supervised_pair_training.local.json',
        'eval/supervised_pair.local.json','eval/supervised_pair_summary.json','eval/supervised_pair_v2.local.json',
        'eval/supervised_pair_v2_summary.json','eval/pair_cross_negative_notes.json','eval/pair_coverage_notes.json',
        'eval/answerability.local.json','eval/supervised_pair_split.json','src/librarian/calibration_data.py',
        'src/librarian/audit_calibration_data.py']
    fingerprint=lambda:{p:sha(ROOT/p) for p in paths}
    hashes=fingerprint();protocol=read(paths[0])
    if hashes[paths[2]]!=read(paths[1])['dataset_sha256']:raise ValueError('Unbound annotation dataset')
    for raw,summary in [(paths[3],paths[4]),(paths[5],paths[6])]:
        if hashes[raw]!=read(summary)['raw_sha256']:raise ValueError('Unbound prior experiment')
    cross=read(paths[7])
    if hashes[paths[9]]!=cross['source_raw_sha256']:raise ValueError('Unbound cross negatives')
    metadata={}
    for ids,lang,family in [
        ('aq01 aq02 aq03','cs','random_forest'),('aq04 aq05 aq06','en','logistic_regression'),
        ('aq07 aq08 aq09','pl','dbscan'),('mi01 mi02 mi03','cs','decision_tree'),
        ('mi04 mi05 mi06','en','kmeans'),('mi07 mi08 mi09','pl','pca'),
        ('mi10 mi11 mi12','cs','svm'),('db01','cs','missing_values'),
        ('db02','en','leakage'),('db08','en','feature_scale'),('gc04','cs','ml_definition'),
        ('sp01 sp02 sp03','cs','naive_bayes'),('sp04 sp05 sp06','en','tfidf'),
        ('sp07 sp08 sp09','pl','knn'),('vc01 vc02 vc03','en','svm'),
        ('vc04 vc05 vc06','cs','random_forest'),('vc07 vc08 vc09','pl','pca')]:
        for key in ids.split():metadata[key]=(lang,family)
    rows=[];query_metadata={}
    excluded=read(paths[10])['excluded_training_question_ids']
    def add(key,p,language,family,versions,study):
        row={k:p[k] for k in ['query','input','text','source_path','label','reason']}
        row.update({'id':key,'language':language,'family':family,'fitted_versions':versions,'study':study,
            'target':1 if row['label']=='direct' else 0 if row['label'] in ('topic_only','irrelevant') else None,
            'all_known_inspected':True})
        query_metadata[query_key(row['query'])]=(language,family)
        rows.append(row)
    original_training=read(paths[2])['pairs']
    for p in original_training:
        lang,family=metadata[p['question_id']]
        if p['derived']:lang='en' if int(p['id'].split('_')[-1]) in (3,4,9,10) else 'cs'
        fitted=['v1','v2'] if p['target'] is not None and p['question_id'] not in excluded else []
        add('annotations:'+p['id'],p,lang,family,fitted,'coverage_annotations')
    for p in read(paths[3])['rows']:
        lang,family=metadata[p['question_id']]
        add('pilot_v1:'+p['id'],p,lang,family,[],'inspected_v1_check')
    for p in read(paths[5])['rows']:
        lang,family=metadata[p['question_id']]
        add('pilot_v2:'+p['id'],{**p,'text':p['input']},lang,family,[],'source_informed_v2_check')
    prior={r['id']:r for r in read(paths[9])['rows']};derived=read(paths[8])['derived_positive_questions']
    for n,c in enumerate(cross['pairs'],1):
        q=prior[c['query_id']]['query'] if 'query_id' in c else derived[c['derived_query_index']-1][2]
        key,rank=c['negative_source'];p=prior[key]['results'][rank-1]
        lang,family=query_metadata[query_key(q)]
        add('cross:'+str(n),{'query':q,'text':p['text'],'input':body(p),'source_path':p['source_path'],
            'label':c['label'],'reason':c['reason']},lang,family,['v2'],'meaningful_cross_negatives')
    identities=defaultdict(list)
    for r in rows:identities[(query_key(r['query']),r['input'])].append(r)
    conflicts=[[r['id'] for r in group] for group in identities.values() if len({r['label'] for r in group})>1]
    duplicates=[[r['id'] for r in group] for group in identities.values() if len(group)>1]
    rows=group_pairs(rows);components=[]
    for key in sorted({r['component'] for r in rows}):
        group=[r for r in rows if r['component']==key]
        components.append({'id':key,'pairs':len(group),'role':group[0]['role'],
            'fitted_versions':group[0]['component_fitted_versions'],
            'labels':dict(Counter(r['label'] for r in group)),
            'languages':sorted({r['language'] for r in group}),
            'families':sorted({r['family'] for r in group}),
            'sources':sorted({r['source_path'] for r in group})})
    clean=[r for r in rows if not r['component_fitted_versions']]
    quality=coverage(clean,protocol['minimums'])
    checks={'total_pairs':len(rows),'labels':dict(Counter(r['label'] for r in rows)),
        'historically_fitted_pairs':sum(bool(r['fitted_versions']) for r in rows),
        'source_query_connected_components':len(components),
        'largest_component_pairs':max(c['pairs'] for c in components),
        'fit_connected_pairs':len(rows)-len(clean),'clean_calibration_candidate_pairs':len(clean),
        'clean_candidate_coverage':quality,'duplicate_pairs':duplicates,'label_disagreements':conflicts,
        'untouched_test_count':0,'threshold_selected':None,
        'calibration_status':'blocked_data_requirements' if not quality['eligible'] or conflicts else 'candidate_data_only_no_final_test',
        'production_changed':False,'broad_release_accepted':False}
    if hashes!=fingerprint():raise ValueError('Inputs changed during audit')
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'checks':checks,'components':components,'rows':rows}
    RAW.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUMMARY.write_text(json.dumps({k:data[k] for k in ['created_at','hashes','checks','components']}|
        {'raw_sha256':sha(RAW)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render(data);print(json.dumps(checks,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
