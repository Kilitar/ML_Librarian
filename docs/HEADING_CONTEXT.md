# Source-adjacent heading context

Current extension: `adjacent-heading-v2` also permits one standalone `st.latex`
formula between heading and body, within the same three-line bound. See
`METRIC_CHOICE.md`. The v1 experiment below remains frozen; use
`AdjacentHeadings(allow_formula=False)` to reproduce its context associations.

This repairs missing **source context**, without rewriting the query, adding
answer text, changing model weights, updating the index or lowering thresholds.
It does not certify the factual correctness of course material.

## Rule and provenance

`heading_context.py` reads only the immutable static extraction in Librarian's
`data/normalized/documents.jsonl`. It sorts Streamlit literal parts by source
line; AST traversal order is not necessarily source order. Only an entire
single-line Markdown heading, directly preceding the body among extracted parts
and at most three source-code lines away, is eligible. No intervening extracted
part, cross-source association, notebook/code execution or generated heading is
allowed. Context records include its source path, heading locator, extraction
SHA256 and `adjacent-heading-v1` version.

Ordinary weak passages (original whole-query score below .20) may be scored again
with that heading prepended to the same body. Use the higher real model prediction
for the same original question. Keep the base score and heading score separately
for inspection; do not replace the evidence score with an E5 score or source
bonus. Strong passages, decomposed comparisons and parameter subquestions keep
their existing scores. Other candidates may change relative order, so preservation
of their own scores is not a promise of unchanged top-five ranking.

The app exposes the original heading and its locator above the excerpt. The
excerpt and chunk ID still identify the original body; source viewing and
hash-verified downloads are unchanged. Source filters apply to candidates before
scoring; heading context is from that same permitted source. Visitor queries are
not written to the context catalog.

## Specific repair and remaining work

For `Why should I standardize features before PCA, and what can happen if I do not?`,
the correct paragraph already existed, but its immediately preceding source
heading was absent from the reranker input. Adding the real heading
`Proč je Standardizace (StandardScaler) povinná?` changes its score from about
.021 to .277, making the direct variance-dominance explanation the first result
with supported availability. No PCA/source ID is hardcoded in production logic.

The support gate remains evidence-v4 with .10/.20 boundaries. A different input
representation can change score distributions; the paired experiment checks
known unrelated requests and new formulations, but is not independent calibration
or human acceptance. Some PCA formulations and spam-filter error-cost coverage
can still be weak. The Polish soup request and contradictory source advice remain
separate issues. The frozen acceptance-v1 results are never overwritten or called
a newly passed release. BYOK generation remains deferred.

## Inspect and reproduce

Validation: 30 full-search pairs changed only the original English PCA status
(no_support→supported). Forty fixed-passage replays changed no status. No absent
question newly became supported, and no supported valid question became
no_support in these checks. Top 1 changed for the repaired English PCA, the new
Polish PCA formulation (broad summary→direct explanation), and the known ambiguous
Czech control (still uncertain). The new English comparable-scales formulation
still leads with a clustering passage; supported availability is not answer
accuracy. 89 unit tests and six actual AppTest submissions passed, including
visible heading context and source filtering. The heading itself was matched by
static AST inspection to the SHA-verified snapshot original; this does not verify
its factual claims. See tracked `eval/heading_context_summary.json`.

Production enables heading context by default; instantiate
`PassageReranker(use_headings=False)` on an index for an explicit baseline. Missing
optional extraction context retains base reranking; invalid base/new model output
cannot be promoted through context. The frozen run precedes default promotion and
these invalid/missing-input guards; actual form results match its after IDs.

`compare_heading_context.py` shares baseline candidate predictions across paired
full-search arms; the context arm scores only eligible additional inputs. Thirty
full-search questions include the prior 24 development formulations, five newly
fixed formulations and the known `Which is better?` ambiguity control (not fresh
evidence). Another 40 historical questions replay their fixed five passages only,
which does not validate full retrieval behavior on those 40 queries.

Run `.venv/Scripts/python.exe src/librarian/compare_heading_context.py` from the
Librarian workspace. First run freezes code/input hashes and all excerpts in
ignored `eval/heading_context.local.json`; subsequent runs regenerate the report
without overwriting raw results. Use a new output path for another run.

Full queries, before/after excerpts, actual source headings and separate scores:
<http://localhost:8765/eval/heading_context_review.local.html>.
