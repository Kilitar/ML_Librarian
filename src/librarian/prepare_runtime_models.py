"""Explicit pinned public-weight preparation before offline query execution."""
from huggingface_hub import snapshot_download
from domain_guard import ENCODER_REVISION
from rerank import MODEL_ID, REVISION, CACHE


def prepare():
    common=['config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','sentencepiece.bpe.model','sentence_bert_config.json','config_sentence_transformers.json','modules.json','1_Pooling/config.json']
    for model,revision in [('intfloat/multilingual-e5-small',ENCODER_REVISION),(MODEL_ID,REVISION)]:
        snapshot_download(repo_id=model,revision=revision,cache_dir=str(CACHE),token=False,allow_patterns=common,max_workers=2)


if __name__=='__main__':prepare()
