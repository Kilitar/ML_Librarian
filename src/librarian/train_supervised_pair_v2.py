"""Eight meaningful-query hard negatives; frozen reciprocal full-chunk benchmark."""
import gc
import hashlib
import html
import json
import random
import time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import torch
from transformers import AutoTokenizer,AutoModelForSequenceClassification
from safetensors.torch import load_file,save_file

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'eval/supervised_pair_v2.local.json'
SUMMARY=ROOT/'eval/supervised_pair_v2_summary.json'
REPORT=ROOT/'eval/supervised_pair_v2_review.local.html'
WEIGHTS=ROOT/'.cache/supervised_pair_v2/trainable.safetensors'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def body(p):return (p['heading_context']['text']+'\n\n' if p.get('heading_context') else '')+p['text']


def evaluate(rows,field,threshold):
    direct=[r for r in rows if r['label']=='direct'];negative=[r for r in rows if r['kind']=='meaningful' and r['label']!='direct']
    nuisance=[r for r in rows if r['kind']=='nonsense'];bad=[];correct=[]
    for key in dict.fromkeys(r['question_id'] for r in direct):
        a=next(r[field] for r in direct if r['question_id']==key)
        b=next(r[field] for r in negative if r['question_id']==key)
        if a>b:correct.append(key)
    for key in dict.fromkeys(r['question_id'] for r in nuisance):
        if any(r[field]>=threshold for r in nuisance if r['question_id']==key):bad.append(key)
    return {'direct_found':sum(r[field]>=threshold for r in direct),'direct_total':len(direct),
        'direct_recall':sum(r[field]>=threshold for r in direct)/len(direct),
        'meaningful_contrast_correct':correct,'meaningful_negative_false_positives':[r['id'] for r in negative if r[field]>=threshold],
        'nonsense_supported_queries':bad,'all_negative_false_positives':[r['id'] for r in rows if r['label']!='direct' and r[field]>=threshold]}


def render(data):
    esc=lambda v:html.escape(str(v))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supervised pair v2</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}</style>',
        '<h1>Stejná smysluplná otázka, správná i zavádějící pasáž</h1>',
        '<p>V2 přidává8 označených negativních párů k původním40. Původní model, uložený v1 a v2 porovnáváme na18 kurátorovaných párech:6 přímých,6 tematických bez požadovaného vztahu,6 nesmyslných. Stejný dokument je kladný pro jednu otázku a záporný pro druhou. Anotace Codex, nikoli lidská/faktická přejímka.</p>',
        '<p>Otázky jsou sestaveny podle doložených zdrojů PŘED tréninkem/skórováním, nejsou nezávislým testem vyhledávání. Původní draft otázek se zachoval, chybějící důvody nebyly přeznačeny na přímé odpovědi. Skóre nejsou pravděpodobnost správné odpovědi.</p>',
        '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a> · <a href="/eval/supervised_pair_review.local.html">Pilot v1</a></p>',
        '<h2>Pevná kritéria a výsledek</h2><pre>'+esc(json.dumps(data['checks'],ensure_ascii=False,indent=2))+'</pre>']
    for r in data['rows']:
        page.append(f"<article><h3>{esc(r['id'])} · {esc(r['label'])}</h3><blockquote>{esc(r['query'])}</blockquote><p>{esc(r['reason'])}</p><p>{esc(r['source_path'])} · {esc(r['chunk_id'])} · {r['tokens']} tokenů</p><p>Původní {r['base']:.4f} · v1 {r['v1']:.4f} · v2 {r['v2']:.4f}</p><pre>{esc(r['input'])}</pre></article>")
    page.append('<h2>Osm nových trénovacích kontrastů</h2>')
    for c in data['contrasts']:
        page.append('<article><blockquote>'+esc(c['query'])+'</blockquote><p>'+esc(c['reason'])+'</p><h3>Přímá odpověď</h3><pre>'+esc(c['positive_input'])+'</pre><h3>Tematická, ale neodpovídající pasáž</h3><pre>'+esc(c['negative_input'])+'</pre></article>')
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if RAW.exists():
        s=read('eval/supervised_pair_v2_summary.json')
        if sha(RAW)!=s['raw_sha256']:raise ValueError('Frozen result hash mismatch')
        render(read('eval/supervised_pair_v2.local.json'));print('Frozen results preserved; rendered only.');return
    if SUMMARY.exists() or WEIGHTS.exists():raise FileExistsError('Preserve partial trial; use a new version')
    paths=['config/supervised_pair_v2_experiment.json','eval/supervised_pair_v2_questions.json',
        'eval/supervised_pair_v2_contrasts.json','eval/pair_cross_negative_notes.json','eval/pair_coverage_notes.json',
        'eval/pair_coverage_judgments.json','eval/supervised_pair_training.local.json','eval/supervised_pair_split.json',
        'eval/answerability.local.json','eval/supervised_pair_summary.json',
        '.cache/supervised_pair_v1/trainable.safetensors','data/normalized/chunks_curated.jsonl',
        'src/librarian/train_supervised_pair_v2.py']
    fingerprint=lambda:{p:sha(ROOT/p) for p in paths}
    hashes=fingerprint();config=read(paths[0]);spec=read(paths[2]);notes=read(paths[3])
    if hashes[paths[8]]!=notes['source_raw_sha256']:raise ValueError('Unbound negative annotations')
    if hashes[paths[6]]!=read(paths[5])['dataset_sha256']:raise ValueError('Unbound original training data')
    if hashes[paths[10]]!=read(paths[9])['checkpoint_sha256']:raise ValueError('Unbound v1 weights')
    excluded=read(paths[7])['excluded_training_question_ids']
    train=[p for p in read(paths[6])['pairs'] if p['target'] is not None and p['question_id'] not in excluded]
    original={r['id']:r for r in read(paths[8])['rows']};derived=read(paths[4])['derived_positive_questions'];contrasts=[]
    for n,c in enumerate(notes['pairs'],1):
        q=original[c['query_id']]['query'] if 'query_id' in c else derived[c['derived_query_index']-1][2]
        nk,nr=c['negative_source'];pk,pr=c['positive_source'];negative=original[nk]['results'][nr-1];positive=original[pk]['results'][pr-1]
        if not any(p['query']==q and p['input']==body(positive) and p['target']==1 for p in train):raise ValueError('Missing same-query direct control')
        train.append({'id':'cross_'+str(n),'query':q,'input':body(negative),'target':0,'label':c['label'],
                      'source_path':negative['source_path'],'reason':c['reason']})
        contrasts.append({'query':q,'positive_input':body(positive),'negative_input':body(negative),'reason':c['reason']})
    if len(train)!=48 or len({(p['query'],p['input']) for p in train})!=48:raise ValueError('Unexpected training count/duplicate')
    catalog={p['chunk_id']:p for p in [json.loads(s) for s in (ROOT/paths[11]).read_text(encoding='utf-8').splitlines()]}
    test=[]
    for group in spec['groups']:
        for question in group['questions']+[group['nonsense']]:
            for n,key in enumerate(group['chunks']):
                doc=catalog[key];positive=question.get('positive')==n
                test.append({'id':question['id']+'_'+str(n+1),'question_id':question['id'],'query':question['query'],
                    'kind':'meaningful' if 'positive' in question else 'nonsense','group':group['id'],
                    'label':'direct' if positive else 'topic_only','reason':question['reason'],
                    'input':doc['text'],'chunk_id':key,'source_path':doc['source_path'],'text_sha256':digest(doc['text'])})
    overlap=[r['id'] for r in test if any(r['query']==p['query'] or r['input']==p['input'] for p in train)]
    if overlap:raise ValueError('Exact train/test overlap: '+repr(overlap))
    torch.set_num_threads(min(8,torch.get_num_threads()))
    options=dict(revision=config['revision'],cache_dir=str(ROOT/'.cache/hf'),local_files_only=True,trust_remote_code=False,token=False)
    tokenizer=AutoTokenizer.from_pretrained(config['base_model'],**options)
    enc=lambda p:tokenizer(p['query'],p['input'],truncation=False)
    train_enc=[enc(p) for p in train];test_enc=[enc(p) for p in test]
    if any(len(e['input_ids'])>config['max_tokens'] for e in train_enc+test_enc):raise ValueError('Complete pair exceeds budget; do not silently truncate')
    def fresh_model():return AutoModelForSequenceClassification.from_pretrained(config['base_model'],use_safetensors=True,**options).eval()
    def predict(model):
        result=[];model.eval()
        with torch.inference_mode():
            for start in range(0,len(test_enc),config['batch_size']):
                batch=tokenizer.pad(test_enc[start:start+config['batch_size']],padding=True,return_tensors='pt')
                values=torch.sigmoid(model(**batch).logits.reshape(-1))
                if not torch.isfinite(values).all():raise ValueError('Nonfinite prediction')
                result.extend(values.tolist())
        return result
    model=fresh_model();base=predict(model)
    state=load_file(str(ROOT/paths[10]));allowed=(f'roberta.encoder.layer.{len(model.roberta.encoder.layer)-1}.','classifier.')
    if not all(k.startswith(allowed) for k in state):raise ValueError('Invalid v1 parameter names')
    if model.load_state_dict(state,strict=False).unexpected_keys:raise ValueError('Unexpected v1 keys')
    v1=predict(model);del model,state;gc.collect()
    random.seed(config['seed']);np.random.seed(config['seed']);torch.manual_seed(config['seed'])
    model=fresh_model();last=len(model.roberta.encoder.layer)-1
    for name,p in model.named_parameters():p.requires_grad_(name.startswith(f'roberta.encoder.layer.{last}.') or name.startswith('classifier.'))
    block=[p for n,p in model.named_parameters() if p.requires_grad and not n.startswith('classifier.')]
    head=[p for n,p in model.named_parameters() if p.requires_grad and n.startswith('classifier.')]
    optimizer=torch.optim.AdamW([{'params':block,'lr':config['learning_rate_last_block']},{'params':head,'lr':config['learning_rate_classifier']}],weight_decay=config['weight_decay'])
    positives=sum(p['target'] for p in train);loss_fn=torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor((len(train)-positives)/positives))
    losses=[];start_time=time.perf_counter()
    for epoch in range(config['epochs']):
        model.eval();model.roberta.encoder.layer[-1].train();model.classifier.train();order=torch.randperm(len(train)).tolist();epoch_loss=[]
        for start in range(0,len(order),config['batch_size']):
            idx=order[start:start+config['batch_size']];batch=tokenizer.pad([train_enc[n] for n in idx],padding=True,return_tensors='pt')
            y=torch.tensor([train[n]['target'] for n in idx],dtype=torch.float32);optimizer.zero_grad(set_to_none=True)
            loss=loss_fn(model(**batch).logits.reshape(-1),y)
            if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(block+head,config['max_grad_norm']);optimizer.step();epoch_loss.append(float(loss.detach()))
        losses.append(float(np.mean(epoch_loss)));print('epoch',epoch+1,'loss',round(losses[-1],5),flush=True)
    training_seconds=time.perf_counter()-start_time;v2=predict(model)
    rows=[{**r,'tokens':len(e['input_ids']),'base':b,'v1':a,'v2':c} for r,e,b,a,c in zip(test,test_enc,base,v1,v2)]
    metrics={k:evaluate(rows,k,config['threshold']) for k in ('base','v1','v2')};a=metrics['v2'];rule=config['promotion_criteria']
    passed=(len(a['meaningful_contrast_correct'])>=rule['meaningful_contrast_correct_min'] and a['direct_recall']>=rule['direct_recall_min']
        and len(a['meaningful_negative_false_positives'])<=rule['meaningful_negative_false_positive_max']
        and len(a['nonsense_supported_queries'])<=rule['nonsense_supported_queries_max']
        and len(metrics['base']['all_negative_false_positives'])-len(a['all_negative_false_positives'])>=rule['false_positive_reduction_min'])
    checks={'metrics':metrics,'train_count':len(train),'positives':positives,'negatives':len(train)-positives,
        'exact_overlap':overlap,'predeclared_criteria_met':passed,'production_changed':False,'broad_release_accepted':False}
    if hashes!=fingerprint():raise ValueError('Inputs changed during trial')
    WEIGHTS.parent.mkdir(parents=True,exist_ok=True);save_file({n:p.detach().cpu().contiguous() for n,p in model.named_parameters() if p.requires_grad},str(WEIGHTS))
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'checks':checks,'training_seconds':training_seconds,
        'epoch_loss':losses,'checkpoint_sha256':sha(WEIGHTS),'rows':rows,'contrasts':contrasts}
    RAW.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUMMARY.write_text(json.dumps({k:v for k,v in data.items() if k not in ('rows','contrasts')}|{'raw_sha256':sha(RAW)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render(data);print(json.dumps(checks,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
