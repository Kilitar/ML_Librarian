"""Local-only semantic search over the curated, immutable course corpus."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer
from constraints import constraint_adjustment, query_constraints
from diversify import select_distinct
from hybrid import LexicalIndex, fuse_scores
from rerank import PassageReranker, candidate_union, expand_neighbors, REVISION as RERANKER_REVISION
from acronyms import requested_acronym, definition_strength
from concepts import definition_query, concept_strength

ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data/normalized/chunks_curated.jsonl"
INDEX_DIR = ROOT / "data/index"
MANIFEST = ROOT / "data/index/multilingual_e5_curated.json"
MODEL_ID = "intfloat/multilingual-e5-small"
CACHE = ROOT / ".cache/hf"
CONCEPT_CUES = (
    "why", "what", "when", "difference", "differ", "explain", "meaning", "choose", "select",
    "co", "proc", "kdy", "rozdil", "vysvetli", "jak vybrat", "co znamena", "co je", "po co",
    "dlaczego", "czym", "rozni sie", "oznacza", "kiedy", "wybrac", "wyjasnij", "roznica",
)
PRACTICE_CUES = (
    "exercise", "homework", "assignment", "lab", "example", "sample", "practice", "code",
    "cviceni", "ukol", "priklad", "implement", "kod", "zadanie", "cwiczenie",
    "przyklad", "implementation", "implementace", "implementacja", "praca domowa",
)


def classify_source(document: dict[str, Any]) -> dict[str, str]:
    """Return transparent, path-based learning-role and source-origin labels."""
    path = str(document.get("source_path", "")).replace("\\", "/").lower()
    filename = path.rsplit("/", 1)[-1]
    kind = str(document.get("source_kind", ""))

    if re.search(r"(?:^|[_/ .-])(exercise|homework|lab|assignment)(?:[_./ .-]|$)", path):
        role, role_icon = "Cvičení / úkol", "🧪"
    elif re.search(r"(?:^|[_ .-])(summary|recap|syllabus)(?:[_./ .-]|$)", filename):
        role, role_icon = "Shrnutí / přehled", "📋"
    elif re.search(r"(?:^|[_ .-])(sample|implementation|guide)(?:[_./ .-]|$)", filename):
        role, role_icon = "Příklad / implementace", "🛠️"
    elif "/theory/" in path or re.search(
        r"(?:^|[_ .-])(theory|theoretical|critique|analysis|introduction|principles|works?)(?:[_./ .-]|$)",
        filename,
    ):
        role, role_icon = "Teorie / analýza", "🔎"
    else:
        role, role_icon = "Studijní materiál", "📚"

    if path.startswith("resources/") and (kind == "pdf" or "pdf" in path):
        origin, origin_icon = "Coderslab PDF", "📄"
    elif path.startswith("views/"):
        origin, origin_icon = "Streamlit prezentace", "🖥️"
    elif kind == "notebook_markdown":
        origin, origin_icon = "Notebook", "📓"
    else:
        origin, origin_icon = "Kurzové poznámky", "📚"
    return {
        "source_role": role,
        "source_role_icon": role_icon,
        "source_origin": origin,
        "source_origin_icon": origin_icon,
    }


def query_intent(query: str) -> str | None:
    """Infer whether a natural-language question asks for concepts or practice."""
    normalized = unicodedata.normalize("NFKD", query.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    padded = f" {normalized} "
    if any(f" {cue} " in padded for cue in PRACTICE_CUES):
        return "practice"
    if any(f" {cue} " in padded for cue in CONCEPT_CUES):
        return "conceptual"
    return None


def rank_adjustment(document: dict[str, Any], intent: str | None) -> float:
    """Small transparent reranking prior for useful, intent-matched evidence."""
    text = document.get("text", "").strip()
    adjustment = -0.06 if len(text) < 120 else 0.0
    if document.get("source_kind") == "pdf":
        words = re.findall(r"\b\w+\b", text)
        single_char_ratio = sum(len(word) == 1 for word in words) / max(1, len(words))
        if single_char_ratio > 0.35:
            adjustment -= 0.06

    role = classify_source(document)["source_role"]
    if intent == "conceptual" and role == "Teorie / analýza":
        adjustment += 0.02
    elif intent == "practice" and role in {"Cvičení / úkol", "Příklad / implementace"}:
        adjustment += 0.02
    return adjustment


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
        self.lexical_index = None
        self.passage_reranker = None

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

    def search(self, query: str, *, limit: int = 5,
               match_constraints: bool = True, mode: str = "e5") -> list[dict[str, Any]]:
        query = " ".join(query.split())
        if not query:
            raise ValueError("Enter a non-empty query")
        if len(query) > 1000:
            raise ValueError("Query is longer than the 1,000-character limit")
        if not 1 <= limit <= 10:
            raise ValueError("Result limit must be between 1 and 10")
        if mode not in {"e5", "hybrid", "rerank"}:
            raise ValueError("Unknown retrieval mode")
        original_query = query
        canonical_definition = definition_query(query) if mode == 'rerank' else None
        query = canonical_definition or query
        query_vector = self.model.encode(
            ["query: " + query], normalize_embeddings=True, convert_to_numpy=True,
        )[0]
        scores = self.embeddings @ query_vector
        lexical_scores = np.zeros(len(scores))
        base_scores = scores
        if mode in {"hybrid", "rerank"}:
            if self.lexical_index is None:
                self.lexical_index = LexicalIndex(self.documents)
            lexical_scores = self.lexical_index.scores(query)
            if mode == "hybrid":
                base_scores = fuse_scores(scores, lexical_scores)
        intent = query_intent(query)
        ranking_scores = {
            index: float(base_scores[index]) + rank_adjustment(self.documents[index], intent)
            for index in range(len(scores))
        }
        ranked = sorted(
            range(len(scores)),
            key=ranking_scores.__getitem__,
            reverse=True,
        )
        # Rerank a bounded pool from existing semantic/quality retrieval.
        # The corpus and its embeddings remain unchanged.
        requested = query_constraints(query)
        acronym = requested_acronym(query)
        acronym_strengths = {i: definition_strength(d['text'], acronym) for i, d in enumerate(self.documents)} if acronym else {}
        candidates = ranked[:80] if match_constraints else ranked
        constraint_details = {}
        evidence_scores = {}
        for index in candidates:
            adjustment, reasons = constraint_adjustment(
                self.documents[index], requested, exact_task=(intent == "practice"),
            ) if match_constraints else (0.0, [])
            ranking_scores[index] += adjustment
            constraint_details[index] = {"adjustment": adjustment, "reasons": reasons}
        ranked = sorted(candidates, key=ranking_scores.__getitem__, reverse=True)
        if mode == "rerank":
            candidates = candidate_union(np.asarray([ranking_scores[i] for i in range(len(scores))]), lexical_scores)
            candidates = expand_neighbors(self.documents, candidates)
            concept_strengths = {}
            if canonical_definition:
                concept_strengths = {i: concept_strength(d['text'], d['source_path']) for i, d in enumerate(self.documents)}
                related = sorted((i for i, strength in concept_strengths.items() if strength >= 2),
                                 key=lambda i: (concept_strengths[i], float(scores[i])), reverse=True)[:24]
                candidates = list(dict.fromkeys(related + candidates))[:120]
            if acronym:
                definitions = sorted((i for i, strength in acronym_strengths.items() if strength > 0),
                                     key=lambda i: (acronym_strengths[i], float(scores[i])), reverse=True)[:24]
                candidates = list(dict.fromkeys(definitions + candidates))[:120]
            try:
                if self.passage_reranker is None:
                    self.passage_reranker = PassageReranker()
                details = self.passage_reranker.score_details(query, [self.documents[i] for i in candidates])
                pair_scores = details["relevance"]
            except (OSError, ValueError, RuntimeError):
                fallback = self.search(original_query, limit=limit, match_constraints=match_constraints, mode="e5")
                for result in fallback:
                    result["retrieval_warning"] = "Přesnější výběr pasáží není dostupný; zobrazuji základní vyhledávání."
                return fallback
            for index, pair_score, full_score in zip(candidates, pair_scores, details["whole_query"]):
                evidence_scores[index] = {"passage_score": float(pair_score), "whole_query_score": float(full_score),
                                          "reranker_revision": RERANKER_REVISION}
                adjustment, reasons = constraint_adjustment(
                    self.documents[index], requested, exact_task=(intent == "practice"),
                ) if match_constraints else (0.0, [])
                ranking_scores[index] = float(pair_score) + rank_adjustment(self.documents[index], intent) + adjustment
                constraint_details[index] = {"adjustment": adjustment, "reasons": reasons}
            ranked = sorted(candidates, key=ranking_scores.__getitem__, reverse=True)
            if canonical_definition:
                ranked.sort(key=lambda i: (concept_strengths[i], ranking_scores[i]), reverse=True)
        if acronym:
            ranked = [i for i in ranked if acronym_strengths[i] >= 0]
            ranked.sort(key=lambda i: (acronym_strengths[i], ranking_scores[i]), reverse=True)
        selected = select_distinct(self.documents, ranked, limit, max_per_source=2 if mode == "rerank" else 1)
        results = []
        for index in selected:
            document = self.documents[int(index)]
            source_labels = classify_source(document)
            results.append({
                "chunk_id": document["chunk_id"],
                "source_path": document["source_path"],
                "locator": document.get("locator"),
                "language": document.get("language"),
                "provenance": document.get("provenance"),
                **source_labels,
                "score": float(scores[int(index)]),
                "lexical_score": float(lexical_scores[int(index)]),
                "retrieval_mode": mode,
                "canonical_query": canonical_definition,
                "concept_evidence": concept_strengths.get(index) if canonical_definition else None,
                "requested_acronym": acronym,
                "acronym_definition": bool(acronym and acronym_strengths[index] == 2),
                **evidence_scores.get(index, {}),
                "ranking_score": ranking_scores[int(index)],
                "constraint_match": constraint_details[index],
                "text": document["text"],
                "streamlit_route": document.get("streamlit_route"),
                "streamlit_title": document.get("streamlit_title"),
                "route_status": document.get("route_status", "unmapped"),
            })
        return results
