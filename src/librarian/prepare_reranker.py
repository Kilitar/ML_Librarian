"""Explicit public-weight download; runtime reranking is offline-only."""
from huggingface_hub import snapshot_download
from rerank import MODEL_ID, REVISION, CACHE


if __name__ == "__main__":
    path = snapshot_download(
        repo_id=MODEL_ID, revision=REVISION, cache_dir=str(CACHE), token=False,
        allow_patterns=["config.json", "model.safetensors", "tokenizer.json",
                        "tokenizer_config.json", "special_tokens_map.json", "sentencepiece.bpe.model"],
        max_workers=2,
    )
    print(f"Pinned offline reranker ready: {path}")
