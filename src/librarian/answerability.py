"""Independent local yes/no scorer. Experimental; not imported by production."""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'config/answerability_experiment.json'


class AnswerabilityScorer:
    def __init__(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.config = json.loads(CONFIG.read_text(encoding='utf-8'))
        self.torch = torch
        torch.set_num_threads(min(8, torch.get_num_threads()))
        options = dict(revision=self.config['revision'], cache_dir=str(ROOT/'.cache/hf'),
                       local_files_only=True, trust_remote_code=False, token=False)
        self.tokenizer = AutoTokenizer.from_pretrained(self.config['model_id'], padding_side='left', **options)
        self.model = AutoModelForCausalLM.from_pretrained(self.config['model_id'], use_safetensors=True,
                                                       dtype=torch.float32, **options).eval()
        self.no = self.tokenizer.convert_tokens_to_ids('no')
        self.yes = self.tokenizer.convert_tokens_to_ids('yes')
        if self.no == self.yes or self.no is None or self.yes is None:
            raise ValueError('Invalid yes/no token mapping')
        self.prefix = '<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be "yes" or "no".<|im_end|>\n<|im_start|>user\n'
        self.suffix = '<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'

    def score(self, query, documents):
        """Keep the question intact; truncate document only, and report truncation."""
        tokenizer = self.tokenizer
        query_ids = tokenizer.encode(query, add_special_tokens=False)
        if len(query_ids) > self.config['max_query_tokens']:
            raise ValueError('Question exceeds independent verifier budget')
        start = tokenizer.encode(self.prefix+'<Instruct>: '+self.config['instruction']+'\n<Query>: '+query+'\n<Document>: ', add_special_tokens=False)
        suffix = tokenizer.encode(self.suffix, add_special_tokens=False)
        budget = self.config['max_tokens']-len(start)-len(suffix)
        if budget < 64:
            raise ValueError('Insufficient document budget')
        inputs, metadata = [], []
        for doc in documents:
            # Body plus genuine adjacent heading; no file name or inferred topic.
            body = doc['text']
            if doc.get('heading_context'):
                body = doc['heading_context']['text']+'\n\n'+body
            ids = tokenizer.encode(body, add_special_tokens=False)
            inputs.append({'input_ids':start+ids[:budget]+suffix})
            metadata.append({'document_tokens':len(ids),'used_document_tokens':min(len(ids),budget),
                             'truncated':len(ids)>budget})
        scores = []
        begin = time.perf_counter()
        with self.torch.inference_mode():
            for offset in range(0,len(inputs),self.config['batch_size']):
                batch = tokenizer.pad(inputs[offset:offset+self.config['batch_size']], padding=True, return_tensors='pt')
                logits = self.model(**batch, use_cache=False, logits_to_keep=1).logits[:,-1,:]
                probabilities = self.torch.softmax(logits[:,[self.no,self.yes]],dim=-1)[:,1]
                if not self.torch.isfinite(probabilities).all():
                    raise ValueError('Invalid verifier output')
                scores.extend(probabilities.tolist())
        return scores, metadata, time.perf_counter()-begin
