# Passage reliability: locally reranked candidate evidence — 2026-10-17

## Production behavior

The Streamlit app and search CLI now explicitly use `mode="rerank"`. The Python
search API retains its E5 default for backward compatibility; callers wanting the
new behavior must request rerank. E5 and the rejected equal-weight hybrid remain
available for reproducible comparisons. If reranker loading/inference fails with
an expected model/runtime error, search falls back to E5 and the UI shows a warning.
No hosted inference, LLM generation, user key or prompt logging was introduced.

## Retrieval and passage selection

1. Build a union of up to 24 E5 candidates and 24 positive TF-IDF candidates.
   This is candidate expansion, not reciprocal-rank fusion as the final score.
2. Add up to two nearby chunks on each side within the same source file, capped
   at 96 total candidates. Preserve each original text, chunk ID and locator.
3. Score question/passage pairs with the pinned local multilingual CrossEncoder.
   Real source path/title is included as context for fragments omitting their topic.
4. If multiple explicit hyperparameters are named, evaluate up to three additional
   versions of the question retaining one named parameter at a time. No answers or
   facts are generated. Use the maximum pair score to retain complementary evidence.
5. Apply the existing small quality/intent/constraint priors. Add tested dataset
   aliases for heart, moons and circles in CZ/EN/PL. Prefer up to two different
   passages per source so complementary explanations can coexist; exact content
   duplicates remain suppressed. A fallback pass may fill with additional distinct
   passages when there are not enough sources.

Scores are sigmoid model outputs plus ordering priors; they can exceed 1 and are
**not calibrated correctness probabilities**. The app now states this explicitly.
Input is capped at 512 model tokens; long code blocks can be truncated for scoring,
although their complete original text is still displayed. Selection does not audit
the factual correctness of the course or guarantee all subquestions are answered.

## Model and installation

Model: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`.
Pinned revision: `1427fd652930e4ba29e8149678df786c240d8825`.
Weights/tokenizer are in ignored `.cache/hf/`. The explicit preparation command
downloads only public safetensors/config/tokenizer files, with no authentication
token and no remote Python code. It never sends course material or queries.
Runtime model loading is `local_files_only=True`, `trust_remote_code=False`.

```powershell
.venv\Scripts\python.exe src\librarian\prepare_reranker.py
.venv\Scripts\python.exe src\librarian\search_curated.py --mode rerank "your query"
```

The installed sentence-transformers package already supports CrossEncoder; no new
package installation was needed. The [publisher's model card](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1)
describes multilingual passage ranking; the [official CrossEncoder API](https://sbert.net/docs/package_reference/cross_encoder/model.html)
documents pair scoring and offline loading. Those descriptions do not establish
quality on our Czech/English/Polish corpus; the local tests below address that.

## Evaluation and acceptance

Acceptance criteria and six fresh formulations were saved before the first
reranker run. Development iterations added source neighbors, parameter separation
and dataset aliases. After freezing the resulting ranking code, 19 known queries
plus the six previously unrun formulations were evaluated. Code hashes were
checked unchanged across that run. No ranking changes followed fresh-result review.

The first 19 left-column results are frozen earlier E5 evidence from the same
corpus (before the new dataset aliases). For the fresh six, the left column is
current E5 with those aliases. The treatment is the whole new pipeline, not an
isolated claim about the neural model alone. Before/after metrics on fresh queries
are intentionally not pooled with the historical development baseline.

| Development question | Prior first useful rank | New first useful rank |
|---|---:|---:|
| SVM C/gamma/overfitting | 4 | 1 |
| Heart RF precision exercise | 1 | 1 |
| Imbalance/accuracy and costly FN | None | 1 |
| Diamond PCA exercise | 1 | 1 |
| Bagging versus boosting | 1 | 1 |
| DBSCAN moons exercise | 3 | 1 |

On these six development questions, useful top-one improves 3/6 → 6/6 and Hit@5
5/6 → 6/6. SVM's first passage explains gamma; result 5 explains both large gamma
and C in a concrete overfitting example. Recall's first two passages separately
address imbalanced accuracy and the metric for costly FN. They are useful evidence,
not complete synthesized answers. The six new formulations also each have a useful
first passage in the provisional Codex review. This is small model-authored QA,
not independent human validation or a representative multilingual benchmark.

Regression checks retained useful first results for diamond-tree and lumbar
logistic exercises. The tree result is now a tuning exercise; the original tree
notebook remains fourth. DBSCAN point definitions move 2 → 1. TF-IDF training
assignment is present but only fifth; lower-ranked alternatives can still be poor.
For the learner's Polish K-Means question, the first result is an implementation
example on spherical blobs; relevant theory follows. Exact duplicates are absent
from all 25 new lists. Out-of-corpus questions still show irrelevant material;
abstention is not implemented and no score threshold was inferred from them.

Local review: `http://localhost:8765/eval/reliability_comparison.local.html`.
It contains exact questions, all old/new excerpts, provenance and measured latency.
`eval/reliability_judgments.json` records reviewed first passages and reasons.
`eval/reliability_acceptance.json` and `eval/reliability_fresh_questions.json` record
the pre-run checks. Full generated evidence is ignored by Git.

```powershell
.venv\Scripts\python.exe src\librarian\compare_reliability.py
```

That comparison requires local `eval/hybrid_comparison.local.json` as its frozen
baseline. Retain it on this machine. On a new checkout, `compare_hybrid.py` can
generate a current E5 baseline, but it is not the same historical run and must be
labelled accordingly. The corpus was not rebuilt in this task.

## Functional checks and remaining work

Twenty-six tests passed, including source-safe neighbors, dual-parameter query
decomposition, complementary same-source passages, missing-model fallback and
inference-error fallback. A real Streamlit AppTest form submission used rerank,
returned the expected imbalance evidence and numeric relevance. A separate render
check verified the visible fallback warning. This is functional testing, not learner
visual acceptance. The local Streamlit was restarted on port 8766.

Measured selection latency across 25 queries: median **3.45 s**, maximum **10.10 s**.
Initial E5 loading/browser time is outside this measurement. Multiple-parameter
questions score more pairs and can be slower. No latency threshold was promised.

Next: learner compares representative results. Then assess abstention and source
factual quality separately; do not treat model scores as confidence. New tuning
must use development data, followed by another frozen question set. All inspected
fresh formulations are now consumed as held-out data. LLM/BYOK remains deferred.
