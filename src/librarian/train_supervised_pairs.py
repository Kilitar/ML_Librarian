"""Small frozen last-block/head fine-tuning trial. Never modifies production."""
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
from safetensors.torch import save_file
from prepare_supervised_pairs import body

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'eval/supervised_pair.local.json'
SUMMARY=ROOT/'eval/supervised_pair_summary.json'
REPORT=ROOT/'eval/supervised_pair_review.local.html'
CHECKPOINT=ROOT/'.cache/supervised_pair_v1/trainable.safetensors'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def hydrate_test(retrieval,notes):
    if notes['retrieval_sha256']!=sha(ROOT/'eval/supervised_pair_retrieval.local.json'):
        raise ValueError('Unbound test labels')
    labels={(key,rank):(label,reason) for key,rank,label,reason in notes['reviewed']}
    pairs=[]
    for q in retrieval['rows']:
        for rank,p in enumerate(q['results'],1):
            label,reason=labels[(q['id'],rank)]
            if label not in ('direct','partial','topic_only','irrelevant','unjudgeable'):raise ValueError('Bad label')
            pairs.append({'id':q['id']+'_'+str(rank),'question_id':q['id'],'query':q['query'],
                'kind':q['kind'],'rank':rank,'label':label,'reason':reason,'input':body(p),'text':p['text'],
                'chunk_id':p['chunk_id'],'source_path':p['source_path'],
                'input_sha256':hashlib.sha256(body(p).encode('utf-8')).hexdigest()})
    if len(labels)!=len(pairs):raise ValueError('Missing/extra test labels')
    return pairs


def metrics(rows,field,threshold):
    eligible=[r for r in rows if r['label'] in ('direct','topic_only','irrelevant') and r[field] is not None]
    tp=sum(r['label']=='direct' and r[field]>=threshold for r in eligible)
    fn=sum(r['label']=='direct' and r[field]<threshold for r in eligible)
    fp=sum(r['label']!='direct' and r[field]>=threshold for r in eligible)
    tn=sum(r['label']!='direct' and r[field]<threshold for r in eligible)
    groups={}
    for r in rows:
        if r['kind']=='nonsense':groups.setdefault(r['question_id'],[]).append(r)
    complete={k:v for k,v in groups.items() if len(v)==5 and all(r[field] is not None for r in v)}
    bad=[k for k,v in complete.items() if any(r[field]>=threshold for r in v)]
    return {'tp':tp,'fn':fn,'fp':fp,'tn':tn,'direct_recall':tp/(tp+fn) if tp+fn else None,
        'direct_precision':tp/(tp+fp) if tp+fp else None,'primary_pair_count':len(eligible),
        'complete_nonsense_questions':list(complete),'nonsense_supported_questions':bad,
        'nonsense_false_positive_rate':len(bad)/len(complete) if complete else None}


def render(data):
    esc=lambda s:html.escape(str(s))
    page=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supervised pair pilot</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto;padding:20px;background:#111827;color:#e5e7eb}article{border:1px solid #64748b;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#93c5fd}</style>',
        '<h1>Cílené učení pokrytí otázky — malý experiment</h1>',
        '<p>Provizorní štítky Codex, nikoli lidská přejímka ani ověření pravdivosti zdroje. Trénink mění pouze poslední blok a klasifikační hlavu kopie původního modelu,5epoch; produkce beze změny. Body+skutečný nadpis, bez názvů souborů. Dílčí opora není trénována jako negativní příklad. Nové9 dotazů na NaiveBayes/TF-IDF/kNN bylo fixováno před tréninkem; všech45 pasáží označeno před skóre natrénovaného modelu.</p>',
        '<p>Skóre nejsou kalibrované pravděpodobnosti správnosti. Pár přes512 tokenů je vynechán z tréninku i primárních metrik; žádné tiché zkrácení. Malá a tematicky korelovaná sada nestačí k přejímce.</p>',
        '<p><a href="http://localhost:8766/">Librarian</a> · <a href="/roadmap.html">Roadmapa</a> · <a href="/eval/pair_coverage_review.local.html">Trénovací štítky a důvody</a></p>',
        '<h2>Výsledky a kontroly</h2><pre>'+esc(json.dumps(data['checks'],ensure_ascii=False,indent=2))+'</pre>']
    for row in data['rows']:
        before='přes limit' if row['before'] is None else f"{row['before']:.4f}"
        after='přes limit' if row['after'] is None else f"{row['after']:.4f}"
        page.append(f"<article><h3>{esc(row['id'])} · štítek {esc(row['label'])}</h3><blockquote>{esc(row['query'])}</blockquote><p>{esc(row['reason'])}</p><p>{esc(row['source_path'])} · {esc(row['chunk_id'])} · {row['tokens']} tokenů · původní text-only {before} → učený {after}</p><pre>{esc(row['input'])}</pre></article>")
    REPORT.write_text('\n'.join(page),encoding='utf-8')


def main():
    if RAW.exists():
        summary=json.loads(SUMMARY.read_text(encoding='utf-8'))
        if sha(RAW)!=summary['raw_sha256']:raise ValueError('Frozen raw mismatch')
        render(json.loads(RAW.read_text(encoding='utf-8')));print('Frozen results preserved; rendered only.');return
    if CHECKPOINT.exists() or SUMMARY.exists():raise FileExistsError('Preserve partial trial; use a new version')
    paths=['config/supervised_pair_experiment.json','eval/pair_coverage_notes.json',
        'eval/pair_coverage_judgments.json','eval/supervised_pair_training.local.json',
        'eval/supervised_pair_questions.json','eval/supervised_pair_retrieval.local.json',
        'eval/supervised_pair_test_notes.json','src/librarian/train_supervised_pairs.py',
        'src/librarian/prepare_supervised_pairs.py','eval/supervised_pair_split.json']
    fingerprint=lambda:{p:sha(ROOT/p) for p in paths}
    hashes=fingerprint();config=json.loads((ROOT/paths[0]).read_text(encoding='utf-8'))
    full_train=json.loads((ROOT/paths[3]).read_text(encoding='utf-8'))['pairs']
    split=json.loads((ROOT/'eval/supervised_pair_split.json').read_text(encoding='utf-8'))
    train=[p for p in full_train if p['question_id'] not in split['excluded_training_question_ids']]
    test=hydrate_test(json.loads((ROOT/paths[5]).read_text(encoding='utf-8')),json.loads((ROOT/paths[6]).read_text(encoding='utf-8')))
    train_queries={p['query'] for p in train};train_inputs={p['input_sha256'] for p in train}
    overlap=[p['id'] for p in test if p['query'] in train_queries or p['input_sha256'] in train_inputs]
    if overlap:raise ValueError('Exact train/test overlap: '+repr(overlap))
    torch.set_num_threads(min(8,torch.get_num_threads()))
    random.seed(config['seed']);np.random.seed(config['seed']);torch.manual_seed(config['seed'])
    options=dict(revision=config['revision'],cache_dir=str(ROOT/'.cache/hf'),local_files_only=True,trust_remote_code=False,token=False)
    tokenizer=AutoTokenizer.from_pretrained(config['base_model'],**options)
    model=AutoModelForSequenceClassification.from_pretrained(config['base_model'],use_safetensors=True,**options)
    def encode(p):return tokenizer(p['query'],p['input'],add_special_tokens=True,truncation=False)
    test_enc=[encode(p) for p in test]
    def predict(enc):
        out=[None]*len(enc);model.eval()
        with torch.inference_mode():
            for start in range(0,len(enc),config['batch_size']):
                ids=[n for n in range(start,min(start+config['batch_size'],len(enc))) if len(enc[n]['input_ids'])<=config['max_tokens']]
                if not ids:continue
                batch=tokenizer.pad([enc[n] for n in ids],padding=True,return_tensors='pt')
                scores=torch.sigmoid(model(**batch).logits.reshape(-1)).tolist()
                if not all(np.isfinite(v) for v in scores):raise ValueError('Invalid scores')
                for n,s in zip(ids,scores):out[n]=s
        return out
    baseline=predict(test_enc)
    selected=[(p,encode(p)) for p in train if p['target'] is not None]
    skipped=[p['id'] for p,e in selected if len(e['input_ids'])>config['max_tokens']]
    selected=[(p,e) for p,e in selected if len(e['input_ids'])<=config['max_tokens']]
    positives=sum(p['target'] for p,e in selected);negatives=len(selected)-positives
    if not positives or not negatives:raise ValueError('Both classes required')
    last=len(model.roberta.encoder.layer)-1
    for name,p in model.named_parameters():p.requires_grad_(name.startswith(f'roberta.encoder.layer.{last}.') or name.startswith('classifier.'))
    blocks=[p for n,p in model.named_parameters() if p.requires_grad and not n.startswith('classifier.')]
    head=[p for n,p in model.named_parameters() if p.requires_grad and n.startswith('classifier.')]
    optimizer=torch.optim.AdamW([{'params':blocks,'lr':config['learning_rate_last_block']},
        {'params':head,'lr':config['learning_rate_classifier']}],weight_decay=config['weight_decay'])
    loss_fn=torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(negatives/positives))
    losses=[];begin=time.perf_counter()
    for epoch in range(config['epochs']):
        model.eval();model.roberta.encoder.layer[-1].train();model.classifier.train()
        order=torch.randperm(len(selected)).tolist();losses_epoch=[]
        for start in range(0,len(order),config['batch_size']):
            batch_rows=[selected[n] for n in order[start:start+config['batch_size']]]
            inputs=tokenizer.pad([e for p,e in batch_rows],padding=True,return_tensors='pt')
            targets=torch.tensor([p['target'] for p,e in batch_rows],dtype=torch.float32)
            optimizer.zero_grad(set_to_none=True);logits=model(**inputs).logits.reshape(-1)
            loss=loss_fn(logits,targets)
            if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(blocks+head,config['max_grad_norm']);optimizer.step()
            losses_epoch.append(float(loss.detach()))
        losses.append(float(np.mean(losses_epoch)));print('epoch',epoch+1,'loss',round(losses[-1],5),flush=True)
    seconds=time.perf_counter()-begin
    trained=predict(test_enc)
    rows=[{**p,'tokens':len(e['input_ids']),'before':b,'after':a} for p,e,b,a in zip(test,test_enc,baseline,trained)]
    before=metrics(rows,'before',config['threshold']);after=metrics(rows,'after',config['threshold'])
    rule=config['promotion_criteria']
    passed=(not overlap and after['direct_recall'] is not None and after['direct_recall']>=rule['heldout_direct_recall_min']
        and len(after['complete_nonsense_questions'])==3 and after['nonsense_false_positive_rate']<=rule['heldout_nonsense_false_positive_rate_max']
        and before['nonsense_false_positive_rate']-after['nonsense_false_positive_rate']>=rule['nonsense_false_positive_reduction_min'])
    checks={'before':before,'after':after,'train_test_overlap':overlap,'training_pairs_used':len(selected),
        'reserved_annotation_ids':[p['id'] for p in full_train if p not in train],
        'positive_count':positives,'negative_count':negatives,'training_over_limit':skipped,
        'test_over_limit':[r['id'] for r in rows if r['after'] is None],'predeclared_criteria_met':bool(passed),
        'production_changed':False,'broad_release_accepted':False}
    if hashes!=fingerprint():raise ValueError('Inputs changed during training')
    CHECKPOINT.parent.mkdir(parents=True,exist_ok=True)
    save_file({n:p.detach().cpu().contiguous() for n,p in model.named_parameters() if p.requires_grad},str(CHECKPOINT))
    data={'created_at':datetime.now(timezone.utc).isoformat(),'hashes':hashes,'checks':checks,
        'training_seconds':seconds,'epoch_loss':losses,'trainable_parameters':sum(p.numel() for p in model.parameters() if p.requires_grad),
        'checkpoint_sha256':sha(CHECKPOINT),'rows':rows}
    RAW.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    SUMMARY.write_text(json.dumps({k:v for k,v in data.items() if k!='rows'}|{'raw_sha256':sha(RAW)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render(data);print(json.dumps(checks,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
