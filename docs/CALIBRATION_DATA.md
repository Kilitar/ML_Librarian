# Data audit and development calibration (2026-10-18)

No weights, production rankings, evidence thresholds, UI or index are changed.
This checkpoint replaces another small training run with data provenance,
leakage checks, a fixed-target cutoff diagnostic and a broader annotation pool.

## Existing labels and grouping

The consolidated129 inspected pairs contain35 direct answers,29 partial,
59 topic-only and6 irrelevant. No exact duplicate pair or label disagreement
was found; this does not validate label correctness. All labels remain
provisional Codex coverage judgments, not independent human or factual approval.

`calibration_data.py` joins rows transitively when they share a normalized
question, source path or exact normalized raw passage. It catches copied text
across files and multiple questions from a document, but not every semantic or
near-text duplicate. The resulting10 components include a largest group of81.
48 pairs were actually fitted by v1/v2; their connections reach118 pairs.
Only11 rows lie outside these fit-connected components: two direct, four
negative and five partial. The binary rows are all English/SVM in one component.

This is a **strict source-transfer stress audit for the fine-tuned variants**.
It does not mean every source-overlapping example is unusable for development
calibration of the original model. Librarian's main deployment target is new
questions over the same fixed course; unseen-source transfer is a stricter
additional check. The original MiniLM weights have not been fine-tuned on these
pairs. Distinguish candidate-specific fitting from fitting other variants.

`config/calibration_protocol.json` fixes readiness floors before audit outputs:
30 direct,59 negative,3 languages with both classes,6 families and8 source
components. The entire old pool also has only7 binary components. Floors are
data-readiness diagnostics, not a statistical acceptance guarantee. With zero
errors,59 *independent* negatives would give an iid one-sided95% upper bound
below5%; these correlated authored examples do not justify that guarantee.
All existing examples have been inspected; untouched labeled test count is0.

Audit, component memberships, questions, labels and full excerpts:
<http://localhost:8765/eval/calibration_data_review.local.html>.

## Does a single original-model cutoff even meet the target?

A separate protocol was fixed before rescoring the100 binary development pairs
with the **original pretrained** MiniLM, body plus genuine heading, without
source names. No v1/v2 trained weights are loaded. Labels used to fit other
variants do not constitute weight fitting for this candidate; their provenance
is retained in the raw diagnostic. Partial labels are excluded, none exceeds
the512-token budget, and the reserved test is never scored.

The fixed target is recall>=80% for direct answers and zero empirical false
acceptance among negatives. **No cutoff meets both.** With zero false positives
the maximum direct recall is21/35 (60%). A negative pair scores.9347; the lowest
direct pair scores.0334. Overlapping scores explain why moving a global cutoff
alone cannot meet this target on the development labels.

This is a feasibility diagnostic, not an independent calibrated model, calibrated
probabilities or the production source-aware gate with structural exceptions.
The ML-acronym direct example is protected separately in production. Do not
translate these numbers into production failure rates. Operational threshold
remains null even if a development candidate were found.

All100 pairs/scores and labels:
<http://localhost:8765/eval/base_calibration_diagnostic_review.local.html>.

## Broader new pool and reserved test

`calibration_collection_questions.json` fixes24 meaningful questions,8 each in
CS/EN/PL, spanning19 families: regression metrics, assumptions, optimization,
neural training/activation, preprocessing, text representations, embeddings,
missing values, encoding, leakage, validation, robust statistics and others.
They are authored development data, not a final unseen acceptance test.

The actual current search pipeline collected all five results for every query:
120 full passages. No candidate was hidden or reranked for data cleanliness.
38 passages use previously fit-connected source files,9 are known exact texts,
and none repeats an old query exactly. These are *per-passage* flags, not a claim
that the other82 are independent: after annotation all transitive components
must be recomputed. **Coverage labels are still all null.** Valid questions and
high search scores do not automatically become positive labels.

`calibration_reserved_test_questions.json` reserves12 other questions before
collection. The collector hashes this file and checks query overlap, but never
sends its questions to search/model. No results or labels exist for that test;
it is not completed acceptance. Final evaluation must bind the frozen candidate,
calibration artifact and split first. This is a technical dependency, not a new
user-approval requirement. Model selection must not consume final test outputs.

- Actual queries and all120 results:
  <http://localhost:8765/eval/calibration_collection_review.local.html>.
- Five-way coverage annotation and explicit JSON export:
  <http://localhost:8765/eval/calibration_collection_labels.local.html>.

The sheet stores edits only in page memory until explicit download. Refresh
loses them. No automatic upload, training, visitor-query capture or persistence.
New exports use schema v3 and bind pool/raw SHA, exact query, rank, chunk, source, raw text and actual
heading+body hash. `pair_label_import.py` validates every binding; missing/extra
or reordered pairs, old v1/v2 schemas, changed context, wrong pool and unknown labels
fail. Unreviewed/partial/unjudgeable are never silently negative training labels.
A validated manual export is not verified human approval.

## Reproduce and checks

Use `.venv/Scripts/python.exe src/librarian/<script>.py`:

- `audit_calibration_data.py`: frozen consolidation/group audit, later render only.
- `collect_calibration_pairs.py`: only the allowlisted24 calibration queries;
  fingerprint-bound per-query checkpoint resumes interrupted collection.
  A finished rerun verifies raw SHA and renders without new inference.
- `diagnose_base_calibration.py`: fixed original-model feasibility check;
  completed reruns verify raw SHA and render only.
- `review_answerability.py --pool calibration`: render120 unlabeled pairs;
  default/original still renders125 earlier pairs.
- `pair_label_import.py <export.json> --pool calibration`: validate only;
  never trains, writes accepted labels or declares human approval.

115 unit tests pass, including transitive leakage, tied-score infeasibility,
cutoff boundary behavior, fit/test contamination rejection, invalid scores,
per-language class gaps and annotation integrity. Node VM simulated-DOM checks
pass for both125/120-pair sheets; test exports were reset to entirely unreviewed
before disk writes and import checks confirm zero binary ratings. No real user
ratings were saved. This does not claim browser download/save or visual review.
Frozen input/raw hashes, render-only reruns and HTTP report/app health checks
pass. Production/UI did not change, so no restart or AppTest was needed.

Next: annotate the120 actual outputs, retain partial/topic distinctions, then
recompute groups and candidate-specific train/calibration assignments. Expand
missing language/class/source coverage instead of relaxing floors to make the
old data pass. Keep the12 reserved questions unused during those decisions.
Original acceptance remains not_accepted; BYOK generation stays deferred.


## Coverage annotation checkpoint — 2026-10-18

All120 new passages were read in full and provisionally annotated by Codex:
42 direct,36 partial,34 topic_only,8 irrelevant. Each judgment has a reason in
`eval/calibration_collection_coverage_notes.json`. These are coverage labels,
not independent human approval or factual validation of source assertions.
Partial labels remain excluded from binary training/calibration targets.

`audit_calibration_collection_labels.py` binds every label to frozen query,
rank, chunk, source, locator, body and actual heading hashes through the v3
import validator. It emits a new frozen labeled artifact and a report containing
all120 full passages and reasons; earlier collection/audit artifacts stay intact.
Reruns require identical inputs/artifact and perform no inference.

Report: <http://localhost:8765/eval/calibration_collection_labeled_review.local.html>.

Recomputing transitive query/source/text groups across all249 inspected pairs
finds7 components, largest223. All120 new pairs connect transitively to sources
used by v1/v2, despite only38 having direct known-source flags at collection.
The strict source-transfer pool for these fine-tuned variants therefore stays
at2 direct and4 negative (plus5 partial), one language/component. No new pair
is assigned independent source-transfer calibration for v1/v2.

The original pretrained base has not been fitted on these labels: its combined
inspected development pool has77 direct/107 negative,31 families and both
classes in all3 languages. It still has only5 binary source components against
the unchanged minimum8. New pool alone has42 direct/42 negative and one
component. These counts are not184 independent observations or model accuracy.
Shared sources do not by themselves invalidate new-query evaluation on a fixed
corpus; the strict source-transfer stress question is separate. No eligibility
floor was relaxed, threshold selected, model trained or production policy changed.

Next: expand genuinely distinct source groups and negatives with separately
fixed questions, rather than repeatedly sampling the same broad summary sources.
Keep base fixed-corpus query calibration separate from v1/v2 source-transfer
requirements; finalize candidate/split/calibration artifact before executing the
12 reserved questions. They remain unexecuted/unlabeled. Acceptance stays
not_accepted and BYOK generation deferred.


## Source contrast extension — 2026-10-18

Added27 provisional Codex coverage pairs from9 previously unused source paths:
9 direct and18 topic_only,9 queries in each language. Full passages were read
before authoring contrasting questions. These are SOURCE-INFORMED constructed
pairs, not fresh production-search outputs, a random calibration sample or
independent human approval. Reusing one passage for3 questions does not create
3 independent observations. No model scores were used or produced.

[All27 questions,9 full passages and reasons](http://localhost:8765/eval/source_group_extension_review.local.html).
Tracked notes bind chunk/source/locator/raw-text SHA and full corpus SHA.
`audit_source_group_extension.py` validates all bindings and no exact normalized
query overlap with earlier data or the reserved questions, then regroups all276
pairs. It rejects ANY transitive query/source/exact-text bridge into prior data.
Frozen artifact reruns require identical inputs including audit code; no inference.

There are9 additional disconnected components under the current path/query/text
rule,16 total,14 containing binary labels. Different paths and nonidentical text
can still paraphrase the same course PDF: this is NOT semantic/topic/factual
independence, and source-informed selection can bias calibration distribution.
Combined original-base development pool86direct/125negative now meets numeric
protocol floors, but this is ONLY data readiness, not successful calibration or
model acceptance. The strict v1/v2 source-transfer pool is11direct/22negative,
3languages with both classes,10families/10components; still short of30/59.

All new rows remain inspected development. No fit/calibration split assigned,
threshold selected, model trained, production changed or reserved test executed.
Next: freeze candidate-specific grouping/split and sampling scope before scoring;
for v1/v2 expand actual direct/negative passage coverage without padding repeated
paraphrases to pass counts. For original base distinguish representative retrieval
pairs from constructed contrast stress pairs when reporting calibration results.
The12 reserved questions remain unexecuted/unlabeled; acceptance not_accepted.
