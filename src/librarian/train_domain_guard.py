"""Explicit local training/export from frozen historical synthetic queries."""
import hashlib
import json
from pathlib import Path
import sklearn
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut,cross_val_predict
from sentence_transformers import SentenceTransformer
from domain_guard import ARTIFACT,TRAINING,MODEL_ID,ENCODER_REVISION,VERSION,DIMENSION,ROOT


def main():
    if ARTIFACT.exists():raise FileExistsError('Preserve trained v1; use a new version to retrain')
    import torch
    torch.set_num_threads(min(8,torch.get_num_threads()))
    raw=TRAINING.read_bytes();rows=json.loads(raw)['questions']
    encoder=SentenceTransformer(MODEL_ID,revision=ENCODER_REVISION,cache_folder=str(ROOT/'.cache/hf'),
                                device='cpu',local_files_only=True)
    x=encoder.encode(['query: '+' '.join(r['query'].split()) for r in rows],normalize_embeddings=True,convert_to_numpy=True)
    y=np.asarray([r['in_domain'] for r in rows])
    model=LogisticRegression(C=10,class_weight='balanced',random_state=0)
    loo=cross_val_predict(model,x,y,cv=LeaveOneOut(),method='predict_proba')[:,1]
    model.fit(x,y)
    artifact={'version':VERSION,'encoder_id':MODEL_ID,'encoder_revision':ENCODER_REVISION,'dimension':DIMENSION,
              'training_sha256':hashlib.sha256(raw).hexdigest(),'training_count':len(rows),
              'query_prefix':'query: ','normalized':True,'threshold':.5,'C':10,'class_weight':'balanced','seed':0,
              'sklearn_version':sklearn.__version__,'coefficients':model.coef_[0].tolist(),'intercept':float(model.intercept_[0])}
    ARTIFACT.write_text(json.dumps(artifact,indent=2)+'\n',encoding='utf-8')
    output={'scope':'LOO domain predictions only. Not end-to-end held-out retrieval; topic families correlated.',
            'training_sha256':artifact['training_sha256'],'artifact_sha256':hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
            'rows':[{**r,'loo_score':float(s)} for r,s in zip(rows,loo)]}
    (ROOT/'eval/grey_domain_training.local.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Exported',len(rows),'examples;',len(model.coef_[0]),'coefficients; no neural model weights changed')


if __name__=='__main__':main()
