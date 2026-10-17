"""Small, explicit CZ/EN/PL algorithm and dataset priors for retrieval."""
from __future__ import annotations

import re
import unicodedata


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold().replace("ł", "l"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


ALGORITHMS = {
    "decision_tree": r"decision\s*tree(?:s|regressor|classifier)?|rozhodovac\w*\s+strom\w*|drzew\w*\s+decyzyjn\w*",
    "logistic_regression": r"logistic\s*regression|logistick\w*\s+regres\w*|regres\w*\s+logistycz\w*",
    "linear_regression": r"linear\s*regression|linearn\w*\s+regres\w*|regres\w*\s+liniow\w*",
    "random_forest": r"random\s*forest\w*|nahodn\w*\s+les\w*|las\w*\s+losow\w*",
    "xgboost": r"xgboost|xgbregressor|xgbclassifier",
    "ridge": r"ridge(?:cv)?",
    "lasso": r"lasso(?:cv)?",
    "knn": r"k\s*nn|k\s+nearest\s+neighbou?rs?",
    "kmeans": r"k\s*means|k\s+sredni\w*",
    "dbscan": r"dbscan",
    "pca": r"pca",
    "tfidf": r"tf\s*idf|tfidfvectorizer",
    "bow": r"bag\s+of\s+words|bow|countvectorizer",
    "word2vec": r"word2vec",
    "svm": r"svm|support\s+vector\s+machines?|linearsvc",
}
DATASETS = {
    "heart": r"heart\w*|cardiac\w*|srdecn\w*|kardiolog\w*|serc\w*",
    "moons": r"make\s*moons|moons?|pulmesic\w*|polksiezyc\w*",
    "circles": r"make\s*circles|circles?|kruz\w*|kruh\w*|okreg\w*",
    "diamonds": r"diamonds?|diamant\w*|diament\w*",
    "lumbar": r"lumbar\w*|bederni\w*\s+pater\w*|ledzwiow\w*",
    "concrete": r"concrete\w*|beton\w*",
    "diabetes": r"diabetes\w*|cukrov\w*|cukrzyc\w*",
    "penguins": r"penguins?|tucnak\w*|pingwin\w*",
    "imdb": r"imdb|movie\s+reviews?|filmov\w*\s+recenz\w*|recenz\w*\s+filmov\w*|recenz\w*\s+filmow\w*",
    "housing": r"kc\s+house\w*|king\s+county|seattle|nemovitost\w*|nieruchomos\w*",
}
ALGORITHM_FAMILIES = (
    {"tfidf", "bow", "word2vec"},
    {"pca"},
    {"dbscan", "kmeans"},
    set(ALGORITHMS) - {"tfidf", "bow", "word2vec", "pca", "dbscan", "kmeans"},
)


def detect(text: str, patterns: dict[str, str]) -> set[str]:
    normalized = normalize(text)
    return {name for name, pattern in patterns.items()
            if re.search(r"\b(?:" + pattern + r")\b", normalized)}


def query_constraints(query: str) -> dict[str, set[str]]:
    return {"algorithm": detect(query, ALGORITHMS), "dataset": detect(query, DATASETS)}


def constraint_adjustment(document: dict, requested: dict[str, set[str]], *,
                          exact_task: bool = False) -> tuple[float, list[str]]:
    """Reward matches, penalize explicit alternatives; missing labels are neutral.

    Source path/title provide context to short excerpts, but only text can earn
    the larger match bonus. Multiple requested values are alternatives (e.g. a
    comparison); no inference of negation or universal entity recognition.
    """
    context = " ".join(str(document.get(key) or "")
                       for key in ("source_path", "streamlit_title"))
    adjustment = 0.0
    reasons = []
    for kind, patterns in (("algorithm", ALGORITHMS), ("dataset", DATASETS)):
        wanted = requested[kind]
        if not wanted:
            continue
        in_text = detect(document.get("text", ""), patterns)
        in_context = detect(context, patterns)
        if kind == "algorithm":
            # TF-IDF followed by LogisticRegression is a valid pipeline, not
            # an algorithm mismatch. Compare alternatives at the same stage.
            alternatives = set().union(*(family for family in ALGORITHM_FAMILIES if family & wanted))
            in_text &= alternatives
            in_context &= alternatives
        if exact_task and in_context and not wanted & in_context:
            # An ensemble explaining a single tree is not the requested exercise.
            adjustment -= 0.04
            reasons.append(f"{kind}:different_source")
        elif exact_task and in_text and not wanted & in_text:
            adjustment -= 0.02
            reasons.append(f"{kind}:different_text")
        elif wanted & in_text:
            # Catalogues mentioning many algorithms/datasets are weaker evidence
            # than a passage focused on the requested one.
            adjustment += 0.03 * (len(wanted & in_text) / len(in_text) if exact_task else 1)
            reasons.append(f"{kind}:text_match")
        elif wanted & in_context:
            adjustment += 0.02
            reasons.append(f"{kind}:source_match")
        elif in_context:
            adjustment -= 0.04
            reasons.append(f"{kind}:different_source")
        # No penalty for an unknown/missing entity or an incidental text mention.
    return adjustment, reasons
