# Comparison retrieval tuning

Latest: the bounded prediction-target contextual strategy supersedes the rejected maximum-aspect experiment for recognized regression/classification comparisons. See `CONTEXTUAL_COMPARISON.md`. The rejected experiment and earlier supervised/unsupervised coverage route below are retained for reproduction; they are not the entire current production policy.

This is evaluation-driven retrieval/reranking tuning, specifically query decomposition and coverage-aware reranking. Model weights are unchanged; this is not model fine-tuning.

`comparisons.py` recognizes bounded CZ/EN/PL comparison grammar and extracts two aspects. Reviewed exact domain names can supply canonical aspect queries. Explicit label-presence cues in a learning/grouping context map to supervised/unsupervised learning; that mapping is a domain rule, not learned understanding. Raw normalized aspects remain unchanged otherwise. The original full question is always scored separately.

Each aspect contributes up to 12 semantic and 12 lexical candidates. Union with the original pool is capped at 128. CrossEncoder evaluates the original question, existing parameter variants and two aspects. A greedy ordering first seeks a not-yet-covered aspect with score >= .20; this is a heuristic coverage threshold, not calibrated correctness. Existing content dedup/source diversity still apply. Candidate-level coverage can be lost after dedup/diversification; final returned metadata must be inspected. Scores cannot validate factual content or prove a full comparison.

## Experiment and promotion

Initial raw-aspect trial failed the known Polish labels question; after explicit domain cue mapping, the final experiment used six development cases, three questions fixed after that change, and three regressions. No changes were made during the final paired run; code/question/index hashes were checked. Raw frozen results use the pre-promotion implementation and evidence-v3. The first exploratory trial is not used as a fresh benchmark.

The full experiment is rejected as a production default. Regression/classification comparisons can promote entropy/MSE passages while demoting the direct distinction in the second baseline result. The final three fresh questions do not establish a general gain: Czech supervised/unsupervised top two were already useful and unchanged; English/Polish classification/regression regress in the full experiment. Codex reviewed joint support of the first two passages only, with reasons and text hashes in `eval/comparison_judgments.json`; not independent human validation or full top-five scoring.

Production enables only an exactly recognized supervised/unsupervised pair (including explicit label-presence descriptions). Other comparisons keep the previous pipeline. Inflected names not recognized by the bounded domain layer also keep baseline. API `comparison_tuning=False` disables it; `comparison_experiment=True` opts into the broader rejected experiment. `semantic_layer=False` disables comparison domain rules as well. Fallback preserves the original question and returns E5 with a warning.

Known Polish development case: first two results move from stemming/random search to passages jointly explaining supervised and unsupervised learning. English named comparison also has both sides first, but baseline already supplied them. Do not claim broad unseen improvement from those cases. Six real Streamlit AppTest submissions confirm approved ordering, original regression/classification ordering, clock no_support, ML and partial deep-learning behavior. 55 unit tests pass, including separate whole-question scores and comparison fallback.

## Evidence-v4

The original whole-question score remains the ordinary support signal. The gate now permits an `uncertain` notice with visible excerpts when returned comparison passages have >=.20 aspect evidence for both sides even though whole-question support is weak. It never marks such a case supported from aspect scores alone. Pinned-model/finite whole-score validation still precedes this rule. The Polish case has whole-question score about .018 and is intentionally uncertain rather than hidden. Missing-side evidence does not trigger the rule. This structural availability signal is not proof of a correct relationship between the sides.

## Reproduce

`compare_comparisons.py` runs the full experimental on/off comparison using `eval/comparison_questions.json`; it intentionally does not represent the production allowlist. `render_comparison_review.py` validates frozen raw/passage hashes and combines reviewed experiment excerpts with local production form-check results. Raw data and rendered reports are ignored; a new run requires renewed review if hashes drift.

Review all questions/excerpts: `http://localhost:8765/eval/comparison_review.local.html`. Historical experiment: `eval/comparison_tuning.local.json`; production form checks: `eval/comparison_production.local.json`.

Next: improve comparison evidence using whole-question relevance jointly with aspect coverage and source structure, not maximum aspect score alone. Preserve this rejected baseline, fix new questions before experimentation, and require unseen multilingual improvements before broader promotion. Independent human usefulness review is still pending. Corpus/index/BYOK unchanged.
