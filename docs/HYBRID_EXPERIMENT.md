# TF-IDF/E5 hybrid experiment — 2026-10-17

## Decision

**Keep E5 as the production default.** The hybrid recovers useful evidence for
the previously missed imbalance/false-negative question, but introduces clear
regressions elsewhere. A higher aggregate metric is insufficient to promote it.
No application control or API key was added; the live app continues its E5 path.

## Implementation and reproduction

The optional `mode="hybrid"` lazily builds a TF-IDF matrix over the existing
4,189 chunks (no embedding rebuild, pickle, external call or source change).
It uses accent-insensitive word unigrams/bigrams, sublinear TF, English stopwords,
and at most 100,000 features. The final tokenizer requires at least two characters.

Equal-weight reciprocal-rank fusion uses `k=60`:
`0.5 * 61/(60 + semantic_rank) + 0.5 * 61/(60 + lexical_rank)`.
Only positive lexical matches vote. If the entire query has no lexical matches,
original semantic scores are used. Scores are ordering signals, not probabilities;
hybrid and E5 score magnitudes are not directly comparable. Existing intent,
quality, constraint and content-diversity rules are then applied unchanged.

```powershell
.venv\Scripts\python.exe src\librarian\compare_hybrid.py
.venv\Scripts\python.exe src\librarian\search_curated.py --mode hybrid "your query"
.venv\Scripts\python.exe src\librarian\search_curated.py --mode e5 "your query"
```

Review all 19 queries and their full old/new top-five excerpts:
`http://localhost:8765/eval/hybrid_comparison.local.html`.
Report and JSON are generated locally and ignored by Git. The comparison covers
the nine `holdout_v1` questions (now development data), nine older diagnostic
questions and the learner's exact Polish K-Means query. It is not a sealed test.
All nine E5 top-five ID sequences matched the frozen repaired-corpus checkpoint.

## Two development trials

The initial one-character-token variant promoted OCR-spaced PDF material on the
Polish K-Means question. Its local outputs are retained as
`eval/hybrid_initial.local.json` and `.html`. The final variant excludes isolated
letters; both use the same fixed fusion weights and k. This correction improves
that obvious failure mode but does not repair all relevance regressions.

The six answerable `holdout_v1` queries were provisionally judged again at passage
level. The paired reasons and text hashes are in `eval/hybrid_judgments.json`.
Other regression examples were inspected qualitatively; they are not included in
the aggregate metrics below. Review is Codex-authored, not independent human QA.

| Query | First useful E5 rank | First useful hybrid rank |
|---|---:|---:|
| SVM C/gamma and overfitting | 4 | 5 |
| Heart Random Forest precision exercise | 1 | 1 |
| Accuracy imbalance / costly false negatives | None | 1 |
| Diamond PCA exercise | 1 | 2 |
| Bagging/boosting | 1 | 1 |
| DBSCAN moons exercise | 3 | 2 |

For these six only: Hit@5 5/6 → 6/6; MRR@5 0.597 → 0.700;
useful passages 12/30 → 14/30; useful first results remain 3/6.
These pool metrics do not measure complete answers or corpus-wide recall.
SVM still lacks C's effect in top five. Recall's two main subquestions are covered
by complementary passages, not one complete first result.

Additional regressions matter: DBSCAN point definitions move from rank 2 to 4;
the full TF-IDF movie-training assignment drops out of top five; lumbar logistic
results gain a concrete homework copy-paste warning and a short PDF title;
diamond PCA leads with a student-score visualization. Polish K-Means stops leading
with OCR but still admits unrelated medical passages. Out-of-scope questions
remain unanswerable despite returned passages; no abstention has been implemented.

## Checks and next step

Eighteen tests passed, including lexical OOV fallback, fusion behavior, accent
matching and one-letter OCR handling. All 19 comparisons completed on the same
index; all 38 top-five lists have distinct content keys. The report has 190 cards,
with escaped source content. Existing main-app queries use `mode="e5"` by default.

Next candidate: use lexical retrieval to expand the evidence pool, then evaluate
passage-level question coverage and explicit task constraints before promotion.
Avoid making equal-weight fusion the global default or selecting per-query modes
from these results alone. Define regression acceptance criteria and freeze fresh
questions before a final improvement claim. BYOK remains deferred.
