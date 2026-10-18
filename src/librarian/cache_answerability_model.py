"""Explicit public-model download; the scorer itself always stays offline."""
import os
os.environ['HF_HUB_DISABLE_XET'] = '1'

import hashlib
import json
from pathlib import Path
from huggingface_hub import model_info, snapshot_download

ROOT = Path(__file__).resolve().parents[2]


def main():
    config = json.loads((ROOT/'config/answerability_experiment.json').read_text(encoding='utf-8'))
    files = ['config.json','generation_config.json','tokenizer.json','tokenizer_config.json',
             'vocab.json','merges.txt','model.safetensors','README.md','chat_template.jinja']
    info = model_info(config['model_id'], revision=config['revision'], files_metadata=True, token=False)
    if info.sha != config['revision']:
        raise ValueError('Pinned revision mismatch')
    weights = next(f for f in info.siblings if f.rfilename=='model.safetensors')
    expected = weights.lfs.sha256
    target = Path(snapshot_download(config['model_id'], revision=config['revision'],
        cache_dir=str(ROOT/'.cache/hf'), allow_patterns=files, token=False, max_workers=2))
    with (target/'model.safetensors').open('rb') as stream:
        actual = hashlib.file_digest(stream,'sha256').hexdigest()
    if actual != expected:
        raise ValueError('Published safetensors SHA256 mismatch')
    print('Pinned public model cached; published weight SHA256 verified:', actual)


if __name__=='__main__':main()
