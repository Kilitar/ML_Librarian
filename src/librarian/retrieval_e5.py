from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
ROOT=Path(__file__).resolve().parents[2]
CHUNKS=ROOT/'data/normalized/chunks.jsonl'
CACHE=ROOT/'.cache'/'hf'
INDEX=ROOT/'data/index'/('multilingual_e5_small_sample.npy' if '--sample' in sys.argv else 'multilingual_e5_small_full.npy')
MODEL='intfloat/multilingual-e5-small'

def main():
    docs=[json.loads(x) for x in CHUNKS.open(encoding='utf-8') if x.strip()]
    # Quick prototype mode: deterministic 600-passage sample for model comparison.
    if '--sample' in sys.argv:
        docs=[d for d in docs if d['source_kind'] not in ('python_comment','notebook_code')]
        step=max(1,len(docs)//600)
        docs=docs[::step][:600]
    import torch
    torch.set_num_threads(min(8, torch.get_num_threads()))
    model=SentenceTransformer(MODEL,cache_folder=str(CACHE),device='cpu')
    vecs=model.encode(['passage: '+d['text'] for d in docs],batch_size=96,show_progress_bar=True,normalize_embeddings=True,convert_to_numpy=True)
    np.save(INDEX,vecs.astype('float32'))
    print(f'Encoded {len(docs)} chunks to {vecs.shape}; saved {INDEX}')
    queries=[arg for arg in sys.argv[1:] if arg != '--sample'] or [
      'Proč se mají data před k-NN standardizovat?',
      'Why should features be scaled before k-nearest neighbors?',
      'Dlaczego standaryzujemy dane przed k-NN?',
      'Jak wybrać liczbę klastrów w K-Means?'
    ]
    for q in queries:
        qv=model.encode(['query: '+q],normalize_embeddings=True,convert_to_numpy=True)[0]
        scores=vecs@qv
        print('\nQUESTION:',q)
        for i in np.argsort(scores)[-5:][::-1]:
            d=docs[int(i)]
            print(f"{scores[i]:.3f} | {d['source_path']} | {d['locator']} | {d['text'][:210].replace(chr(10),' ')}")
if __name__=='__main__':main()
