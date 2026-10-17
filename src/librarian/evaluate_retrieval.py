from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import torch
ROOT=Path(__file__).resolve().parents[2]
CHUNKS=ROOT/'data/normalized/chunks.jsonl'; QUESTIONS=ROOT/'eval/retrieval_questions.json'; OUT=ROOT/'eval/retrieval_prototype_results.json'
CACHE=ROOT/'.cache'/'hf'; MODEL='intfloat/multilingual-e5-small'

def main():
    docs=[json.loads(x) for x in CHUNKS.open(encoding='utf-8') if x.strip()]
    docs=[d for d in docs if d['source_kind'] not in ('python_comment','notebook_code')]
    step=max(1,len(docs)//600); docs=docs[::step][:600]
    qs=json.loads(QUESTIONS.read_text(encoding='utf-8-sig'))
    texts=[d['text'] for d in docs]; vectorizer=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=100000,token_pattern=r'(?u)\b\w+\b'); tf=vectorizer.fit_transform(texts)
    torch.set_num_threads(min(8,torch.get_num_threads())); model=SentenceTransformer(MODEL,cache_folder=str(CACHE),device='cpu')
    passages=model.encode(['passage: '+x for x in texts],batch_size=96,show_progress_bar=False,normalize_embeddings=True,convert_to_numpy=True)
    qvecs=model.encode(['query: '+q['query'] for q in qs],batch_size=16,show_progress_bar=False,normalize_embeddings=True,convert_to_numpy=True)
    results=[]
    for qi,q in enumerate(qs):
        row={'id':q['id'],'query':q['query'],'language':q['query_language'],'gold_paths':q['gold_source_paths'],'gold_present_in_sample':any(d['source_path'] in q['gold_source_paths'] for d in docs),'retrievers':{}}
        tf_scores=cosine_similarity(vectorizer.transform([q['query']]),tf).ravel(); e5_scores=passages@qvecs[qi]
        for name,scores in [('tfidf',tf_scores),('e5',e5_scores)]:
            top=np.argsort(scores)[-5:][::-1]; rank=next((r+1 for r,i in enumerate(top) if docs[int(i)]['source_path'] in q['gold_source_paths']),None)
            row['retrievers'][name]={'gold_rank_at_5':rank,'reciprocal_rank_at_5':0 if rank is None else 1/rank,'top5':[{'source_path':docs[int(i)]['source_path'],'locator':docs[int(i)]['locator'],'score':float(scores[int(i)]),'text':docs[int(i)]['text'][:220]} for i in top]}
        results.append(row)
    summary={}
    for name in ('tfidf','e5'):
        rs=[r['retrievers'][name] for r in results if r['gold_present_in_sample']]
        summary[name]={'queries_with_gold_in_sample':len(rs),'mrr_at_5':float(np.mean([r['reciprocal_rank_at_5'] for r in rs])) if rs else None,'recall_at_5':float(np.mean([r['gold_rank_at_5'] is not None for r in rs])) if rs else None}
    out={'scope':'600-passage deterministic sample; compare retrievers on same candidates','queries':len(qs),'sample_passages':len(docs),'excluded_kinds':['python_comment','notebook_code'],'metrics_exclude_queries_without_gold_in_sample':True,'summary':summary,'results':results}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,indent=2)); print('Wrote',OUT)
if __name__=='__main__':main()
