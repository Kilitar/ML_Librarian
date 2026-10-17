"""Local-only semantic search over the curated, immutable course corpus."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data/normalized/chunks_curated.jsonl"
INDEX_DIR = ROOT / "data/index"
MANIFEST = ROOT / "data/index/multilingual_e5_curated.json"
MODEL_ID = "intfloat/multilingual-e5-small"
CACHE = ROOT / ".cache/hf"


def load_chunks(path: Path = CHUNKS) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def corpus_fingerprint(documents: list[dict[str, Any]]) -> str:
    """Fingerprint order and content so a stale index cannot silently be used."""
    digest = hashlib.sha256()
    for document in documents:
        digest.update(document["chunk_id"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(document["text"].encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


class E5SearchIndex:
    def __init__(self, documents: list[dict[str, Any]], embeddings: np.ndarray,
                 model: SentenceTransformer) -> None:
        if embeddings.ndim != 2 or embeddings.shape[0] != len(documents):
            raise ValueError("Index dimensions do not match the curated corpus")
        self.documents = documents
        self.embeddings = embeddings.astype(np.float32, copy=False)
        self.model = model

    @classmethod
    def load(cls) -> "E5SearchIndex":
        if not MANIFEST.is_file():
            raise FileNotFoundError(
                "Curated E5 index is missing. Build it with "
                "python src/librarian/build_curated_index.py"
            )
        documents = load_chunks()
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("model_id") != MODEL_ID:
            raise ValueError("The local search index was built with a different embedding model")
        if manifest.get("corpus_fingerprint") != corpus_fingerprint(documents):
            raise ValueError("The curated corpus changed; rebuild its local search index")
        if manifest.get("document_count") != len(documents):
            raise ValueError("Index manifest document count does not match the corpus")
        index_name = manifest.get("index_file", "")
        if Path(index_name).name != index_name or not index_name.startswith("multilingual_e5_curated_"):
            raise ValueError("Index manifest contains an unsafe index path")
        index_path = INDEX_DIR / index_name
        if not index_path.is_file():
            raise FileNotFoundError("The index referenced by the current manifest is missing")
        embeddings = np.load(index_path, mmap_mode="r", allow_pickle=False)
        if list(embeddings.shape) != manifest.get("shape"):
            raise ValueError("Embedding matrix shape does not match its manifest")
        model = SentenceTransformer(
            MODEL_ID, cache_folder=str(CACHE), device="cpu", local_files_only=True,
        )
        return cls(documents, embeddings, model)

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        query = " ".join(query.split())
        if not query:
            raise ValueError("Enter a non-empty query")
        if len(query) > 1000:
            raise ValueError("Query is longer than the 1,000-character limit")
        if not 1 <= limit <= 10:
            raise ValueError("Result limit must be between 1 and 10")
        query_vector = self.model.encode(
            ["query: " + query], normalize_embeddings=True, convert_to_numpy=True,
        )[0]
        scores = self.embeddings @ query_vector
        selected = np.argsort(scores)[-limit:][::-1]
        results = []
        for index in selected:
            document = self.documents[int(index)]
            results.append({
                "chunk_id": document["chunk_id"],
                "source_path": document["source_path"],
                "locator": document.get("locator"),
                "language": document.get("language"),
                "provenance": document.get("provenance"),
                "score": float(scores[int(index)]),
                "text": document["text"],
                "streamlit_route": document.get("streamlit_route"),
                "streamlit_title": document.get("streamlit_title"),
                "route_status": document.get("route_status", "unmapped"),
            })
        return results
