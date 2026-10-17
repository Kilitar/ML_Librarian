"""Offline TF-IDF evidence and rank fusion; no source or embedding mutation."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class LexicalIndex:
    def __init__(self, documents: list[dict]):
        self.vectorizer = TfidfVectorizer(
            strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True,
            max_features=100_000, token_pattern=r"(?u)\b\w{2,}\b", stop_words="english",
        )
        self.matrix = self.vectorizer.fit_transform([document["text"] for document in documents])

    def scores(self, query: str) -> np.ndarray:
        vector = self.vectorizer.transform([query])
        return (self.matrix @ vector.T).toarray().ravel()


def fuse_scores(semantic: np.ndarray, lexical: np.ndarray, k: int = 60) -> np.ndarray:
    """Equal-weight reciprocal rank fusion, scaled to at most one.

    Zero lexical matches have no lexical vote. An entirely unknown query falls
    back to original cosine scores, preserving all existing ranking priors.
    """
    if semantic.shape != lexical.shape or semantic.ndim != 1:
        raise ValueError("Semantic and lexical scores must be matching vectors")
    if not np.any(lexical > 0):
        return semantic.copy()
    fused = np.zeros(len(semantic), dtype=np.float64)
    for scores, positive_only in ((semantic, False), (lexical, True)):
        order = np.argsort(-scores, kind="stable")
        for rank, index in enumerate(order, 1):
            if positive_only and scores[index] <= 0:
                break
            fused[index] += (k + 1) / (2 * (k + rank))
    return fused
