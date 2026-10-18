# Weak-result ordering

Historical checkpoint: source-adjacent headings subsequently repaired the original
English PCA support error. See `HEADING_CONTEXT.md` for current behavior. To replay
this checkpoint, disable heading context with `PassageReranker(use_headings=False)`
as well as choosing the desired ranking strategy; the frozen report stays intact.

This is a ranking repair, **not** a passed retrieval acceptance. Original PCA
abstention and spam-filter error-cost coverage remain unresolved. The Polish soup
question still receives uncertainty. No corpus, embedding index or model weights
are changed; no provider calls or query rewriting are added.

## Rule

When every candidate's original whole-question crossencoder score is below .10,
use equal reciprocal-rank votes from raw E5 cosine and reranker relevance
(`k=60`). Ignore source/role priors in this narrow fallback: tiny cosine
differences were being overwhelmed by those bonuses. Candidate generation,
source exclusions, deduplication and source diversity still apply. Special
semantic plans, acronym questions and decomposed comparisons keep their existing
ordering. Invalid model metadata cannot activate fusion.

Original `whole_query_score`, `passage_score` and cosine values remain untouched.
`ranking_policy=weak-fusion-v2` identifies the result. The app displays original
whole-question relevance for these cards, because RRF votes near one must not
appear as high evidence support. The existing evidence-v4 gate is unchanged.
Since **all candidates** are below its .10 boundary, changing their subset/order
cannot change an ordinary no_support decision. Ambiguous queries retain their
existing clarification behavior.

The earlier trial at .20 was rejected: a Czech PCA query improved in ordering but
lost the uncertain status when a higher-score weak passage left the returned
five. V2 protects both uncertain and supported results by restricting eligibility
to the existing no-support region. This restriction is an architectural safeguard,
not a newly calibrated confidence threshold.

Default API: `ranking_strategy='weak_fusion'`; `ranking_strategy='reranker'` reproduces
previous ordering. E5/hybrid modes are unchanged. Unknown strategies are rejected.
The gate thresholds are still tied to the pinned reranker, not to RRF or E5.

## Evaluation and limits

Paired experiment: 12 inspected acceptance questions, six inspected diagnostic
questions, six formulations frozen before trial1. The six are now development
data because trial1 was reviewed before choosing the safer v2. No independent
held-out improvement is claimed. Both arms share the exact same candidate
predictions, with no second crossencoder inference or model changes.

The known English PCA question now includes the direct variance-dominance passage
`d82d1087d9b406592ceb` at rank 3 instead of excluding it from all five. Its first
passage remains imperfect and its no_support status remains unchanged. A further
English formulation still retrieves weak material; broad multilingual robustness
is not established. Requests with any candidate whole-query score at least .10
retain their ordering. All 13 supported requests in the 24-query paired run retain
all five IDs/order; all 24 gate statuses are unchanged. Fusion activates for nine
queries. Context-free ambiguous questions may reorder weak matches but retain
clarification status.
Do not reinterpret the frozen acceptance-v1 summary as a newly passed release.

Full before/after excerpts and copyable queries:
<http://localhost:8765/eval/ranking_fusion_v2_review.local.html>.
Rejected trial retained locally at
<http://localhost:8765/eval/ranking_fusion_trial1_review.local.html>.

Reproduce from Librarian with
`.venv/Scripts/python.exe src/librarian/compare_ranking_fusion.py`.
First run freezes ignored `eval/ranking_fusion_v2.local.json` with code/question
and index-manifest hashes. Later runs only regenerate its report. Use a new file
for another experiment. Source text is escaped in the report. All run artifacts
stay in Librarian; the course workspace is not executed or modified.
