# Retrieval acceptance v1 — not accepted

The 12 questions and criteria in `eval/acceptance_v1_questions.json` were fixed before retrieval. The run used unchanged production code/index, no source filters, and no ranking/threshold tuning. Topics: metrics, data preparation, NLP and clustering/PCA. Three out-of-scope questions and one context-free question check abstention. New formulations are not independent human validation or entirely unseen concepts; all reviewed questions now become development data.

## Predeclared checks

| Check | Required | Observed | Result |
|---|---:|---:|---|
| Direct first passage, course queries | >=6/8 | 6/8 | pass |
| Core coverage in first three, course queries | >=7/8 | 6/8 | fail |
| Hard rejection of course queries | 0 | 1 | fail |
| Out-of-scope queries no_support | 3/3 | 2/3 | fail |
| Ambiguous query uncertain | 1/1 | 1/1 | pass |
| Fallback / exact duplicate passages | 0 / 0 | 0 / 0 | pass |
| Original source integrity failures | 0 | 0 (39 files verified) | pass |

Grades are provisional Codex relevance/coverage judgments. Direct core support does not mean complete or factually verified answers. Source SHA-256 confirms original snapshot bytes; it does not certify the source's assertions. Exact dedup does not merge paraphrases (e.g. two quiz feedback passages on stemming).

## Blockers

- **av02:** Precision/recall spam question has relevant definitions, but the first three do not explain the cost of losing legitimate messages versus allowing spam. Final review grades joint core coverage as partial; an initial provisional 7/8 coverage count was corrected to 6/8 without changing criteria or retrieval.
- **av08:** “Why should I standardize features before PCA, and what can happen if I do not?” leads with distance-based clustering; the first three lack PCA variance/scale reasoning. Gate no_support ~.073 incorrectly hard-rejects an answerable question. Later candidates only give a dataset example or clustering advice. This is both retrieval and evidence-availability failure, not just a cosmetic threshold issue.
- **av11:** Polish tomato-soup recipe leads with DBSCAN code and is uncertain ~.103 instead of no_support. It is visible irrelevant evidence, not a generated hallucinated answer. Lowering the gate threshold to rescue PCA would not solve this false uncertainty.
- **Source-quality concern:** av01 first recommends Weighted F1 while the third passage warns against it for minority-class failures. av04 also contains an absolute drop-first recommendation. These need separate source-content review before answer generation; passing relevance checks does not resolve such issues.

Good evidence: av03 directly demonstrates train-only scaler fitting and leakage, av04 distinguishes OHE/ordinal encoding, av05 explains global IDF rarity, av06 explains stemming/lemmatization despite quiz framing, av07 explains DBSCAN noise and no input K. av02 remains partial: false-positive terminology is present, but the required cost-based choice is not explained in the first three.

## Artifacts and reproduction

`evaluate_acceptance.py` refuses to overwrite an existing frozen raw result and checks code/question/index hashes during the run. Use a new evaluation set for future altered retrieval; preserve this baseline. `score_acceptance.py` checks the frozen question/criteria hash, raw file hash, reviewed passage IDs/text hashes, exact content duplicates, fallback status and original source bytes. It creates tracked `eval/acceptance_v1_summary.json` and ignored full review HTML. Changing criteria after retrieval is rejected.

Tracked questions, judgments, summary and scripts remain reviewable without publishing source excerpts. To render all five excerpts locally, use the existing ignored `eval/acceptance_v1_results.local.json` and run `score_acceptance.py`. Report: `http://localhost:8765/eval/acceptance_v1_review.local.html`.

Decision: do not freeze/promote this as an accepted retrieval release; no optional LLM generation yet. Next work targets PCA candidate/context retrieval and cross-domain abstention, preserving these cases as regressions and fixing a different fresh check before further tuning. Human review of representative excerpts remains pending; the report links av01/av04 and the two blockers for focused review.
