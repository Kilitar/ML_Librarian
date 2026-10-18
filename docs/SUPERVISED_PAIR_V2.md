# Same-query contrast pilot v2 (2026-10-18)

**Not promoted.** Eight meaningful-question hard negatives were added to the
original40 binary pairs. V2 fits a new copy of the original pretrained model,
with the same seed17, five epochs, last-block/head learning rates and .50
threshold as v1. It does not continue from the v1 checkpoint. Training uses
25 direct and23 negative pairs. Every new negative has an existing direct
passage for the exact same question, often about the same algorithm.

This removes the possibility of perfectly fitting these contrasts using only
the question or only the document. It does not prove the model learned the
intended relation, and the small Codex-labeled set is not human acceptance.

## Test construction and its limits

The initially fixed draft in `eval/supervised_pair_v2_questions.json` is
preserved. Targeted source inspection did not establish complete explanations
for all drafted why-questions (RBF scale sensitivity, PCA centering rationale
and curved manifolds). Those passages were not forced into positive labels.

The final `supervised_pair_v2_contrasts.json` is explicitly **source-informed**,
fixed before any base/v1/v2 scores or v2 fitting. It is a curated pair benchmark,
not blind query selection, independent topic/source acceptance, or current
end-to-end retrieval. Do not count it as the initial draft's successful test.

Three groups use two full source chunks each:

- SVM kernel trick versus OvO/OvR model counts and voting.
- Random Forest OOB evaluation versus MDI feature importance and bias.
- PCA mean subtraction versus eigenvalue/eigenvector meanings.

Each group has two meaningful questions with reciprocal direct/wrong-relation
passages and one nonsensical question against both passages:18 pairs total,
six direct and12 negative. The same passage is positive for one question and
negative for the other. No exact training question or input text overlaps test.
Topics/source families remain correlated with the training data. All complete
pairs fit512 tokens (test maximum360); none is silently truncated.

## Result

| Check at fixed .50 threshold | Original text-only | V1 | V2 |
|---|---:|---:|---:|
| Direct answers recognized | 5/6 | 4/6 | 4/6 |
| Correct reciprocal ordering | 6/6 | 6/6 | 6/6 |
| Wrong-relation false positives | 0/6 | 0/6 | 0/6 |
| Nonsense questions passing | 0/3 | 0/3 | 0/3 |

The original model already solves the negative examples in this small curated
test. There is no demonstrated false-positive gain. Both trained variants lose
the direct PCA centering passage at the threshold: original .542, v1 .413,
v2 .380. The direct PCA eigenvalue explanation remains missed by all three
(.075/.102/.080), despite being ranked above the wrong paragraph. Relative
ordering and absolute coverage decisions are different tasks; neither a good
ordering nor a conservative score proves answerability.

V2 training takes10.87seconds; training loss .446→.395. Predeclared promotion
criteria fail. No threshold/epoch/LR retuning used this test. The small pilot
does not justify further production weight changes or a general accuracy claim.
Base here is raw body-only scoring at.50, not production source-aware ranking
or its.10/.20 evidence gate.

Full queries, all18 excerpts and original/v1/v2 scores, plus the eight training
contrasts and reasons:
<http://localhost:8765/eval/supervised_pair_v2_review.local.html>.

## Reproduce and validation

Run `.venv/Scripts/python.exe src/librarian/train_supervised_pair_v2.py` from
Librarian. The first run validates original annotation/v1 checkpoint hashes,
same-query positive controls, distinct48 training pairs, no exact test overlap,
complete token budgets and unchanged input fingerprints. Weights are saved only
under ignored `.cache/supervised_pair_v2/trainable.safetensors`. Tracked summary
binds input/raw/checkpoint hashes. Reruns verify raw SHA and render only.

Run `check_supervised_pair_checkpoint.py --trial v2` to validate checkpoint SHA,
allowed parameter names, unchanged first encoder block and three reloaded scores.
This persistence check passes; render-only replay and106 existing unit tests
pass. Report HTTP200 and app healthok are verified separately. No AppTest/restart
is needed because production search, gate, UI, index and model are unchanged.

Next: stop treating more tiny last-block runs as a release path. Expand and
review representative pair coverage, including difficult real retrieval outputs,
then separate training, calibration and untouched testing. The new reciprocal
pairs are now inspected development/regression examples. A calibration split
must be distinct from fitting and final acceptance; do not move the threshold
to repair the observed PCA scores. Original acceptance remains not_accepted and
BYOK generation stays deferred.
