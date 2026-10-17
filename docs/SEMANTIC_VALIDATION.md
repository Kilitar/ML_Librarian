# Passage usefulness checkpoint

This checkpoint changes no retrieval, vocabulary, thresholds, corpus or index. It reviews the frozen 18-question paired experiment, then runs nine questions fixed before retrieval against production. The reviewer is Codex: these are provisional judgments, not independent human validation. All inspected questions are now development/regression data.

Rubric applies to the first passage only: `direct` explicitly supports the core question; `partial` is related context/example without the core explanation; `off_topic` does not address the requested meaning. Direct support is not full-answer coverage or source-factual verification. We do not compute Precision@5 or Recall because the other ranks are not comprehensively labeled.

## Frozen paired experiment

36 first-passage judgments across 18 queries and two variants:

| Variant | Direct | Partial | Off-topic |
|---|---:|---:|---:|
| Shared baseline without domain rules | 10 | 5 | 3 |
| Full experimental domain rewrites | 12 | 6 | 0 |

This is a developmental ablation with shared source/intent priors and algorithm/dataset constraints, not a pure-model benchmark. The full experimental layer differs from the production allowlist. Three languages per topic are correlated; do not treat them as 18 independent topics. Classification's catalogue contains a short explicit definition and receives `direct`, although it is less useful than the fuller Czech explanation. Regression's MSE derivation receives `partial`; its Czech definition displaced by canonicalization is also partial under the strict generic-regression rubric because it only defines linear regression. The rationale, not only the category count, explains why those rewrites remain disabled.

## Nine fresh formulations

Six course questions use comparisons, practical scenarios and paraphrases outside the simple definition grammar. None receives a semantic canonical rewrite. Three additional questions ask for exchange rates, bread baking and train departure times.

Among six course questions, first passages are 4 direct, 1 partial and 1 off-topic. All three out-of-scope questions receive `no_support`. No course question is hard rejected: four `supported`, two `uncertain`. Exact expected availability status matches 7/9, but that count is not answer accuracy.

Specific limits:

- sf02: overfitting definition directly explains the train/test symptom, but the gate is uncertain (~.163). Useful conservative false uncertainty.
- sf04: first passage is a house-price tree example; the explicit regression/classification distinction is rank 3. Gate is supported (~.242), which must not be interpreted as first-passage completeness.
- sf06: Polish labels-vs-groups comparison leads with stemming/lemmatization. Unsupervised definition is rank 3, supervised definition rank 5. Gate is uncertain (~.170). Useful evidence is present but poorly ranked and split.
- Source statements about neural-network approximation and other facts were not externally verified. Labels judge relevance, not factual soundness.

## Reproduction and review

Run `evaluate_semantic_fresh.py` for the tracked fixed questions; it freezes model results and verifies code/question/index hashes did not change during the run. It does not relabel passages. Run `render_semantic_validation.py` to validate the frozen raw/text hashes against `eval/semantic_passage_judgments.json`, render all excerpts with reasons, and rebuild `eval/semantic_validation_summary.json`. The renderer rejects a changed raw file or stale passage judgment; a new run may require explicit new review, never automatic judgment reuse.

Review: `http://localhost:8765/eval/semantic_validation.local.html`. Raw local excerpts remain ignored by Git. Tracked judgments include chunk IDs, SHA-256 text hashes, grades and reasons. This is a reproducible local audit when the ignored frozen inputs exist, not a self-contained public corpus export.

Next: improve comparison-intent and complementary-evidence ordering, starting with supervised-vs-unsupervised and regression-vs-classification examples. Preserve current baseline and verify on newly fixed unseen formulations before promoting changes. A larger synonym list alone cannot resolve split comparison evidence. Independent human usefulness review remains pending; keep LLM generation deferred.
