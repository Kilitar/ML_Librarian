from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from search import CACHE, INDEX_DIR, MANIFEST, MODEL_ID, corpus_fingerprint, load_chunks


def main() -> None:
    documents = load_chunks()
    if not documents:
        raise SystemExit("Curated corpus is empty; run build_curated_corpus.py first")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(min(8, torch.get_num_threads()))
    model = SentenceTransformer(MODEL_ID, cache_folder=str(CACHE), device="cpu")
    vectors = model.encode(
        ["passage: " + doc["text"] for doc in documents],
        batch_size=96, show_progress_bar=True,
        normalize_embeddings=True, convert_to_numpy=True,
    ).astype("float32", copy=False)
    if vectors.ndim != 2 or vectors.shape[0] != len(documents):
        raise RuntimeError("Embedding output dimensions do not match curated corpus")

    fingerprint = corpus_fingerprint(documents)
    index_name = f"multilingual_e5_curated_{fingerprint[:16]}.npy"
    index_path = INDEX_DIR / index_name
    fd, temp_index = tempfile.mkstemp(prefix=".curated-index-", suffix=".npy", dir=INDEX_DIR)
    try:
        with os.fdopen(fd, "wb") as output:
            np.save(output, vectors, allow_pickle=False)
        os.replace(temp_index, index_path)
    finally:
        if os.path.exists(temp_index):
            os.unlink(temp_index)

    metadata = {
        "model_id": MODEL_ID,
        "corpus_fingerprint": fingerprint,
        "index_file": index_name,
        "document_count": len(documents),
        "shape": list(vectors.shape),
        "dtype": str(vectors.dtype),
        "normalized": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": "course-2026-10-17-v1",
    }
    fd, temp_manifest = tempfile.mkstemp(prefix=".curated-manifest-", suffix=".json", dir=MANIFEST.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            json.dump(metadata, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.replace(temp_manifest, MANIFEST)
    finally:
        if os.path.exists(temp_manifest):
            os.unlink(temp_manifest)
    print(f"Built {vectors.shape[0]} × {vectors.shape[1]} local embeddings at {index_path}")


if __name__ == "__main__":
    main()
