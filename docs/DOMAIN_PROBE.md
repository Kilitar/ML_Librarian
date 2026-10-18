# Domain classification diagnostic — not promoted

Historical unconditional-classifier diagnostic. A later, strictly conditional
grey-band use is described in `GREY_DOMAIN_GUARD.md`; the unrestricted classifier
remains rejected and this original report is preserved.

The cross-topic acceptance remains **not accepted**. No production retrieval,
gate thresholds, corpus, index, UI or model weights changed in this checkpoint.

## Experiment

`evaluate_domain_probe.py` fits balanced logistic regression (C=10, seed=0,
decision threshold .5) on normalized, frozen E5 query embeddings. Its 37 examples
come from historical abstention checks: 25 supported and 12 absent questions.
Three ambiguous questions were excluded. Availability labels are only provisional
domain labels; this is not a separately annotated domain dataset. Similar topics
and formulations are correlated. No fitted model is installed or persisted.

Leave-one-out classification: **35/37** correct at .5. The two failures are
important: `PCA` scores .464 (incorrectly outside the domain), while
`How do I repair a leaking kitchen faucet?` scores .574 (incorrectly inside).
Therefore this classifier is unsuitable as a hard rejection gate. Its output is
not calibrated answer confidence or evidence sufficiency.

The inspected acceptance questions are development data. The Polish soup question
scores .486, barely below .5; the English PCA question scores .803. Fixing those
two examples by itself would not demonstrate reliability. Domain membership also
does not repair passage ordering or establish that an answer is present.

Six new formulations were fixed in `eval/support_repair_questions.json` before
testing. Unchanged production availability statuses match all six expectations
(three supported, three no_support); classifier domain predictions also match.
This is **not** six correct answers: the first PCA passages remain broad summaries,
with direct variance explanation second for Czech and absent from Polish top 3.
No independent human or factual-quality acceptance is claimed. These formulations
are now inspected regression data.

## PCA diagnosis

The direct variance/units explanation already exists in chunk
`d82d1087d9b406592ceb`. For the failing English question it ranks third by raw
dense similarity (.856), but pinned crossencoder relevance is only .021 with
metadata, .080 with text alone. Expanding PCA to its English name does not
consistently rescue it. Adding neighboring text improves some scores but does
not establish a reliable repair. Lowering a global support threshold would also
admit more unrelated results. None of these probes was promoted.

The next retrieval experiment should compare candidate ranking and model
robustness on multilingual formulations, keeping whole-query support separate
from topic membership. Spam-filter error-cost coverage remains unresolved.
BYOK generation is still deferred.

## Reproduce and inspect

Run from the Librarian workspace:

```powershell
.venv/Scripts/python.exe src/librarian/evaluate_domain_probe.py
```

The first run requires the frozen local acceptance output and offline models;
it freezes full results plus input hashes in ignored
`eval/domain_probe_results.local.json`. Subsequent runs preserve this file and
only regenerate its report. Use a new output name for a new experiment.
Training questions, fresh questions and diagnostic code are tracked; local raw
excerpts and HTML remain ignored.

Review every query and all five actual excerpts at
<http://localhost:8765/eval/domain_probe_review.local.html>. The acceptance section
replays the immutable v1 output; the six fresh questions were run against unchanged
production. The report is a diagnostic, not a new release acceptance.
