# Error-cost context for choosing precision or recall

The retrieval planner recognizes a bounded explicit priority between the two
named metrics, plus a stated application context. It does not learn new model
weights, rewrite the original question or change support thresholds. Generic
definitions, unrecognized wording, absent context and recognized negation preserve
the existing search. CZ/EN/PL patterns are reviewed but not universal language
understanding; ambiguous Czech `přesnost` alone is not treated as precision.

## Evidence coverage

When the original winning passage is already supported (whole-query score at
least .20), retain it first. Among the existing candidate pool, score at most12
passages that mention the requested error class and a literal word/prefix application
anchor in their body. The auxiliary question asks when to minimize false positives
for precision, or false negatives for recall, in the explicitly requested context.
This is a versioned domain relationship, not an answer source.

One qualifying explanation (facet score at least .20) may move to second place
when the strongest such passage is missing from the existing first three. Source
filters, content deduplication and source diversity still apply. No extra corpus
search, new candidate pool or unbounded context expansion is used. If the facet
fails, retain base ranking. `metric_choice_tuning=False` disables this coverage
step; `semantic_layer=False` also disables it.

The facet score is recorded separately as `metric_choice_facet_score`; it never
replaces `whole_query_score` or supplies support to an unsupported original
question. The original winner stays first. The app labels promoted passages as
additional error-cost context instead of presenting the auxiliary score as the
answer's confidence. The promoted context excerpt opens alongside the first
result, so the rationale is immediately visible. Original query scores remain auditable.

## Source structure

The useful spam example explicitly says that a false positive can delete an
important work email. Its source heading, `Precision`, is separated from the body
by one standalone `st.latex` formula. `adjacent-heading-v2` permits exactly that
bridge: same source, heading→formula→body, no other extracted part, at most three
source-code lines in total. Only the original heading is prepended; the formula
locator is retained as provenance. Arbitrary intervening text/code and distant or
cross-source headings remain ineligible. `AdjacentHeadings(allow_formula=False)`
reproduces v1 context for comparisons.

The original body, chunk IDs, immutable snapshot, E5 index and model weights are
unchanged. Source viewing/downloads remain static; no course code is executed.
As elsewhere, source integrity does not validate factual correctness of claims
in the teaching materials.

## Evaluation and limits

Final paired run:36 full searches and40 fixed-passage replays, with zero gate
status changes. Context was added for av02 (known English spam), mc01 (Czech spam),
mc03 (recall/screening) and mc05 (English automated spam). In each, the original
winner remains first. The known spam rationale is now second; heading-only
ablation did not bring it into the first3. Static AST inspection matched the
heading, formula call and body to the SHA-verified snapshot original.

The Polish formulation mc02 still lacks the direct lost-email rationale in its
first3; no score threshold or query alias was patched to force that case. Reverse
recall mc03 still leads with a precision-oriented clinical passage, followed by
the added recall cost explanation; do not claim top1 quality improved. The new
adversarial metric/soup question remains no_support in both arms, while the older
plain Polish soup query av11 remains uncertain. These are different cases.

97 unit tests and seven actual AppTest form submissions passed, including EN/CZ
context, unchanged PL behavior, reversed FN priority, adversarial absence, PCA
regression and hiding summaries. All query/form IDs match frozen after results;
hidden summary context never leaks. See `eval/metric_choice_summary.json` for
hashes, limited judgments and provenance audit. This is not new release acceptance.

`compare_metric_choice.py` compares the previous pipeline, heading-only ablation
for recognized priority queries, and heading+coverage. Thirty inspected questions
are development checks; six metric formulations were fixed before this change,
including reverse recall priority and an adversarial metric/soup request. Another
40 historical questions replay their fixed five passages only; they are not full
retrieval checks. No independent-topic or human acceptance is claimed.

The known English spam question keeps its first recommendation, then includes
the explicit lost-work-email rationale. This improves joint evidence coverage;
the first recommendation alone is still partial. The frozen acceptance-v1 output
is preserved and is not replaced with a passed release. Out-of-course abstention,
including nonsensical application contexts, still requires separate evaluation.
BYOK remains deferred.

Run `.venv/Scripts/python.exe src/librarian/compare_metric_choice.py`. First run
freezes input/code hashes and full excerpts in ignored `eval/metric_choice.local.json`;
later runs only regenerate the report. Use a new output name for a new run.
All queries, before/heading-only/after excerpts, auxiliary questions and scores:
<http://localhost:8765/eval/metric_choice_review.local.html>.
