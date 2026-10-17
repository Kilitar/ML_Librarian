from __future__ import annotations
import json, re, sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
ROOT=Path(__file__).resolve().parents[2]
CHUNKS=ROOT/'data/normalized/chunks.jsonl'
INDEX=ROOT/'data/index/tfidf_index.json'

def main():
    docs=[json.loads(x) for x in CHUNKS.open(encoding='utf-8') if x.strip()]
    vectorizer=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=250000,token_pattern=r'(?u)\b\w+\b')
    matrix=vectorizer.fit_transform([d['text'] for d in docs])
    # Persist a portable sparse matrix and vocabulary without pickle.
    import scipy.sparse as sp
    import numpy as np
    sp.save_npz(ROOT/'data/index/tfidf_matrix.npz',matrix)
    (ROOT/'data/index/tfidf_vocabulary.json').write_text(json.dumps({k:int(v) for k,v in vectorizer.vocabulary_.items()},ensure_ascii=False),encoding='utf-8')
    INDEX.write_text(json.dumps({'snapshot':'course-2026-10-17-v1','documents':len(docs),'features':int(matrix.shape[1]),'vectorizer':{'ngram_range':[1,2],'sublinear_tf':True}},indent=2),encoding='utf-8')
    print(f'Indexed {matrix.shape[0]} chunks, {matrix.shape[1]} terms; sparse nnz={matrix.nnz}')
    for q in sys.argv[1:]:
        qv=vectorizer.transform([q]); sims=cosine_similarity(qv,matrix).ravel(); top=np.argsort(sims)[-3:][::-1]
        print('\nQUERY:',q)
        for i in top: print(f"{sims[i]:.3f} | {docs[i]['source_path']} | {docs[i]['locator']} | {docs[i]['text'][:180].replace(chr(10),' ')}")
if __name__=='__main__':main()
