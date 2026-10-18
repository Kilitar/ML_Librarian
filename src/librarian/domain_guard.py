"""Optional, bounded domain signal; never a replacement for passage evidence."""
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
MODEL_ID='intfloat/multilingual-e5-small'
ENCODER_REVISION='614241f622f53c4eeff9890bdc4f31cfecc418b3'
VERSION='grey-domain-v1'
DIMENSION=384
ARTIFACT=ROOT/'config/grey_domain_v1.json'
TRAINING=ROOT/'eval/domain_probe_training.json'


def query_hash(query):
    return hashlib.sha256(' '.join(query.split()).encode('utf-8')).hexdigest()


class DomainGuard:
    def __init__(self, raw, training_sha256):
        data=json.loads(raw)
        if (not isinstance(data,dict) or data.get('version')!=VERSION or data.get('encoder_id')!=MODEL_ID
                or data.get('encoder_revision')!=ENCODER_REVISION or data.get('dimension')!=DIMENSION
                or data.get('training_sha256')!=training_sha256 or data.get('query_prefix')!='query: '
                or data.get('normalized') is not True or data.get('threshold')!=.5):
            raise ValueError('Incompatible domain artifact')
        self.weights=np.asarray(data['coefficients'],dtype=float)
        self.intercept=float(data['intercept'])
        if self.weights.shape!=(DIMENSION,) or not np.isfinite(self.weights).all() or not math.isfinite(self.intercept):
            raise ValueError('Invalid domain coefficients')
        self.sha256=hashlib.sha256(raw).hexdigest()

    def signal(self, vector, query, encoder_revision):
        vector=np.asarray(vector,dtype=float)
        if (encoder_revision!=ENCODER_REVISION or vector.shape!=(DIMENSION,)
                or not np.isfinite(vector).all() or abs(float(np.linalg.norm(vector))-1)>.001):
            return None
        value=float(vector@self.weights+self.intercept)
        score=1/(1+math.exp(-max(-40,min(40,value))))
        return {'version':VERSION,'encoder_revision':ENCODER_REVISION,'artifact_sha256':self.sha256,
                'query_sha256':query_hash(query),'score':score}

    def outside(self, signal, query):
        if not isinstance(signal,dict):return False
        score=signal.get('score')
        return bool(signal.get('version')==VERSION and signal.get('encoder_revision')==ENCODER_REVISION
                    and signal.get('artifact_sha256')==self.sha256 and signal.get('query_sha256')==query_hash(query)
                    and isinstance(score,(int,float)) and not isinstance(score,bool)
                    and math.isfinite(score) and 0<=score<.5)


@lru_cache(maxsize=1)
def load_guard():
    return DomainGuard(ARTIFACT.read_bytes(),hashlib.sha256(TRAINING.read_bytes()).hexdigest())


def make_signal(vector, query, encoder_revision):
    try:return load_guard().signal(vector,query,encoder_revision)
    except (OSError,ValueError,KeyError,TypeError):return None


def outside_domain(results, query):
    try:
        signals=[r.get('domain_signal') for r in results]
        if not signals or signals[0] is None or any(s!=signals[0] for s in signals):return False
        return load_guard().outside(signals[0],query)
    except (OSError,ValueError,KeyError,TypeError):return False
