# Supervised query–passage pilot (2026-10-18)

This checkpoint performs actual supervised fine-tuning of a separate copy of
the current MiniLM reranker. It does not change production or claim a successful
answerability verifier.

## Provisional coverage labels

All selected passages were read in full before assigning labels. The tracked
`eval/pair_coverage_notes.json` and hash-bound `pair_coverage_judgments.json`
contain58 pairs:25 direct,13 partial,20 topic_only. Annotations are by Codex,
not independent human judgments. Coverage does not validate the source's facts,
absolute scaling claims, metric recommendations or numeric results.

Fourteen direct questions were authored from exactly the same passages used in
nonsensical negative pairs. This prevents a passage-only classifier from solving
the task. The thirteen partial pairs, including transferable food applications,
are excluded from binary fitting, rather than being labeled nonsense.

Five known db08 k-NN scale pairs are reserved for audit before fitting. Two of
their bodies also occur in the new retrieval, so reserving all five both keeps
that query family out of training and prevents exact text overlap. The split is
recorded in `eval/supervised_pair_split.json`; no test passage was removed.

**A valid question is not evidence that its returned passages answer it.** All
five db08 results discuss other issues (dimensionality, initialization, ANN or
eps selection) rather than why numeric ranges dominate distances. The prior
Qwen trial's frozen preservation criterion still fails as recorded; this new
coverage audit does not retroactively relabel that trial accepted. It explains
why a downgrade alone was insufficient to diagnose a model regression.

See all58 queries, excerpts, reasons and split statuses:
<http://localhost:8765/eval/pair_coverage_review.local.html>.

## Fixed experiment

`config/supervised_pair_experiment.json` and nine questions were fixed before
fitting. Three new triples concern Naive Bayes, TF-IDF and k-NN: nonsense,
technical question, meaningful application. All45 returned passages were read
and labeled before seeing fine-tuned scores. Only four are direct positives
(three TF-IDF, one k-NN); no returned passage answers the Naive Bayes assumption
question. This is an observed retrieval gap, not an invalid question.

There is zero exact question/body overlap after the pre-fit audit split.
Two source files still overlap between train and check (the general Scikit-learn
reference and DBSCAN implementation guide). This is not independent source or
topic-level acceptance, and four direct positives cannot establish broad recall.

The pilot uses40 binary pairs (25 positive/15 negative), full question+body and
actual adjacent heading, no source names. It updates only the final transformer
block and classifier (1,922,689 parameters) for5 epochs with fixed seed17,
last-block LR5e-5, head LR5e-4, balanced BCE and threshold.50. No model input
exceeds512tokens here. Partial pairs do not enter primary binary metrics.

Weights live only in ignored `.cache/supervised_pair_v1/trainable.safetensors`;
the base cached model and production index/ranking/gate are unchanged. Safe
checkpoint SHA and all input/raw hashes are recorded in the tracked summary.
The measured training took15.05seconds. No epoch selection or hyperparameter /
threshold tuning used the check predictions.

## Result: no demonstrated classification improvement

At the fixed threshold, base text-only and fine-tuned models both have:

- Direct recall3/4 (75%) and precision3/5 (60%).
- Two false-positive pairs,23 true negatives,29 primary pairs;16 partial pairs
  excluded and still fully visible.
- One of three nonsense questions passes: the Polish soap/k-NN request.
- Its two high scores fall .818→.594 and .811→.592, still above.50.
- Direct k-NN scale explanation remains missed (.149→.151).

Loss falls .416→.338 on training, but held-out classification counts do not
improve. Predeclared criteria fail; no promotion or broad release acceptance.
Base here means text-only pair scores at.50, not the production source-aware
ranking or its.10/.20 evidence gate. Do not report these as production metrics.

All45 new pairs, labels, reasons, original/fine-tuned scores and full excerpts:
<http://localhost:8765/eval/supervised_pair_review.local.html>.

## Reproduce and validation

From the Librarian checkout:

1. `prepare_supervised_pairs.py` binds exact source/text hashes and preserves
   frozen annotation/retrieval outputs on rerun.
2. `train_supervised_pairs.py` uses fixed notes and split, refuses exact overlap,
   records fingerprints before/after and never overwrites a trained checkpoint.
   After a successful run, reruns verify raw SHA and render only.
3. `render_pair_coverage.py` checks dataset SHA and displays all annotations.
4. `check_supervised_pair_checkpoint.py` verifies checkpoint SHA, allowed weight
   names, unchanged first encoder block and reproduction of three stored scores
   from a fresh model load. It is a persistence check, not fresh accuracy evidence.

Use `.venv/Scripts/python.exe src/librarian/<script>.py`. Existing106 unit tests
pass; checkpoint reload and render-only preservation pass. HTTP reports200 and
app healthok; no AppTest/restart because production/UI code did not change.

Manual label export now uses schema `answerability-pair-review-v2`: direct,
partial, topic_only, irrelevant, unjudgeable. This separates real partial answer
content from topic-only matches. V1 exports must not be silently reinterpreted.
The125-pair page remains unfilled and memory-only until explicit export. JS
selection/count/note/export and default labels were rechecked with a simulated
DOM; browser download/save and human visual review are not claimed.

## Next data improvement

The small pilot still permits a **query-only shortcut**: almost every negative
training query is nonsensical. Same-passage positive controls are necessary but
do not remove this second shortcut. `eval/pair_cross_negative_notes.json`
prepares eight additional wrong-relation pairs where the **same meaningful
question** has both a direct and a negative passage, often about the same
algorithm. These are provisional reviewed candidates, prepared after the pilot,
not used in v1 or evidence of measured improvement.

Next training needs these balanced relation contrasts and more direct positive
coverage across algorithms, with a new version and different pre-fixed test
relations. These inspected nine questions are now development/regression data.
Original acceptance remains not_accepted; no BYOK generation is added.
