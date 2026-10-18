"""Verify persisted trainable weights reproduce frozen scores on representative pairs."""
import hashlib
import json
import argparse
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForSequenceClassification
from safetensors.torch import load_file

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--trial',choices=['v1','v2'],default='v1')
    trial=parser.parse_args().trial
    prefix='supervised_pair' if trial=='v1' else 'supervised_pair_v2'
    summary=json.loads((ROOT/f'eval/{prefix}_summary.json').read_text(encoding='utf-8'))
    checkpoint=ROOT/f'.cache/supervised_pair_{trial}/trainable.safetensors'
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest()!=summary['checkpoint_sha256']:raise ValueError('Checkpoint hash mismatch')
    raw=ROOT/f'eval/{prefix}.local.json'
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=summary['raw_sha256']:raise ValueError('Raw hash mismatch')
    config=json.loads((ROOT/f'config/{prefix}_experiment.json').read_text(encoding='utf-8'))
    options=dict(revision=config['revision'],cache_dir=str(ROOT/'.cache/hf'),local_files_only=True,trust_remote_code=False,token=False)
    torch.set_num_threads(min(8,torch.get_num_threads()))
    model=AutoModelForSequenceClassification.from_pretrained(config['base_model'],use_safetensors=True,**options).eval()
    tokenizer=AutoTokenizer.from_pretrained(config['base_model'],**options)
    state=load_file(str(checkpoint))
    allowed=(f'roberta.encoder.layer.{len(model.roberta.encoder.layer)-1}.','classifier.')
    if not state or not all(k.startswith(allowed) for k in state):raise ValueError('Unexpected trainable weight name')
    unchanged=model.roberta.encoder.layer[0].attention.self.query.weight.detach().clone()
    result=model.load_state_dict(state,strict=False)
    if result.unexpected_keys:raise ValueError('Unexpected checkpoint keys')
    assert torch.equal(unchanged,model.roberta.encoder.layer[0].attention.self.query.weight)
    rows=json.loads(raw.read_text(encoding='utf-8'))['rows']
    keys=['sp05_1','sp07_1','sp08_5'] if trial=='v1' else ['vc01_1','vc04_2','vc08_2']
    selected=[next(r for r in rows if r['id']==key) for key in keys]
    encoded=tokenizer([r['query'] for r in selected],[r['input'] for r in selected],padding=True,truncation=False,return_tensors='pt')
    with torch.inference_mode():scores=torch.sigmoid(model(**encoded).logits.reshape(-1)).tolist()
    for row,score in zip(selected,scores):
        field='after' if trial=='v1' else 'v2'
        if abs(row[field]-score)>1e-5:raise ValueError('Reloaded score differs: '+row['id'])
    print('Checkpoint SHA, permitted parameter names, frozen first block and three reloaded scores verified.')


if __name__=='__main__':main()
