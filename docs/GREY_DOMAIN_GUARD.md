# Conditional domain guard — limited repair, not retrieval acceptance

`evidence-v5` adds a small learned domain signal only for ordinary reranker
results with best original whole-query score in **[.10,.20)**. If its domain
score is below .5, show no_support instead of uncertain. The known Polish
tomato-soup question now follows this route: original score .1029, domain .4860.
The latter is close to the boundary and is **not** calibrated answer confidence.

Strong results (>=.20), existing no_support (<.10), E5 fallback/unassessed scores,
explicit ambiguity, related-concept evidence, acronym definitions and partial
comparisons retain their previous rules. Domain membership cannot supply evidence,
upgrade weak results, reorder passages or change their scores. The guard is a
conditional safety signal, not an unrestricted domain classifier.

## Model and reproducibility

Balanced logistic regression, C=10, seed0, on frozen multilingual E5 query
embeddings from 37 historical synthetic evaluation questions (25 course,12 absent).
The labels originally described evidence availability and are only provisional
domain labels. Ambiguous training questions are excluded. No dish/forbidden-word
list is used. There was no hyperparameter or threshold tuning on the new set.

`config/grey_domain_v1.json` stores 384 numeric coefficients, intercept, exact
training-file SHA, encoder revision and training configuration. Inference uses
NumPy and a sigmoid; no pickle, remote code, API, model download or visitor-query
training. The neural E5/crossencoder weights and corpus/index remain unchanged.
The separate linear classifier is fitted locally. Training refuses to overwrite
v1; create a new model version for future training.

E5 query encoding is now explicitly pinned to revision
`614241f622f53c4eeff9890bdc4f31cfecc418b3`, which was the existing cached main
revision and sole installed snapshot. This fixes the coordinate system for the
linear weights without rebuilding the index. Prefix `query: `, normalized vectors,
dimension 384, matching training-file bytes and metadata are validated.

Only index instances loaded with that known revision can produce a signal.
Source-filter views retain the binding. The existing original query vector is
reused: no extra embedding/model forward pass per visitor query. Signals bind to
the artifact SHA, encoder revision and whitespace-normalized query hash; all
returned passages must agree. Missing/invalid/stale metadata or unavailable
classifier preserves previous uncertain behavior. Structural exceptions and valid
reranker metadata are checked before the domain signal.

API `domain_guard_tuning=False` disables the signal. Missing optional model files
also preserve the baseline. Runtime does not persist queries or retrain itself.
Run `train_domain_guard.py` only for an explicit new training version; the trained
artifact is already included in Git. Exact training file bytes must match the
artifact. Model changes require a new validation and process restart.

## Evidence and unresolved failures

The fixed new set has 24 formulations (12 course/12 absent) and four known controls.
All 28 were searched with current models. Another 36 outputs from the previous
metric-choice study replay only the policy; no fresh retrieval is claimed for
those 36. Historical leave-one-out diagnostics use old fixed results and are
neither current full retrieval nor independent acceptance.

No new valid question changed from supported/uncertain to no_support. Strong
statuses stayed unchanged. Actual before/after pipeline checks on three queries
confirmed identical five IDs and original scores. 106 unit tests and seven actual
AppTest form submissions passed, including the repaired soup query, uncertain
course query, PCA, acronym, ambiguity, the failing pancake query and source filters.

**The new set had no status changes.** Utility in this experiment is established
only for the inspected, known soup query. No broad generalization claim follows.
The new Polish `Jak zrobić naleśniki?` still receives supported (~.2027), while the
domain classifier also incorrectly puts it inside (.559). Widening the reranker
band alone would not fix it. A valid Polish feature-scale question gd11 remains
no_support (~.0983) even though its domain score is .775; membership must not
manufacture passage support. These are current blockers, not successes.

The classifier alone was previously rejected (LOO 35/37: short PCA and plumbing
errors). Its limited conditional role protects those historical examples, but
does not make the classifier generally reliable. Next: more diverse labeled
out-of-course procedural queries, independent fresh validation before broader
use, and the multilingual retrieval gaps. No global release acceptance, factual
audit or BYOK generation is added; original acceptance-v1 remains frozen.

## Inspect

`evaluate_grey_domain.py` preserves its raw output and only regenerates HTML on
subsequent runs. The frozen run predates enabling the API default and adding
failure highlights to the renderer; actual default-on forms match its IDs/status.
Full queries and all five excerpts, decisions and uncalibrated domain scores:
<http://localhost:8765/eval/grey_domain_review.local.html>.
