# ML Librarian

Standalone multilingual RAG study assistant over a versioned snapshot of the completed Coderslab Data Science course.

## Boundaries
- `D:\Antigravity Projects\Data-Science` is read-only source material.
- All Librarian code, snapshots, environments, indexes, generated data, and caches live in this workspace.
- Course snapshots, normalized content, indexes, `.venv`, caches, and secrets are ignored by Git.
- Source language is Czech/English; query and response language targets are Czech/English/Polish.

## Local retrieval prototype
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-librarian.txt
.\.venv\Scripts\python.exe src\librarian\ingest.py
.\.venv\Scripts\python.exe src\librarian\chunk.py
.\.venv\Scripts\python.exe src\librarian\build_routes.py
.\.venv\Scripts\python.exe src\librarian\attach_routes.py
.\.venv\Scripts\python.exe src\librarian\retrieval_tfidf.py
.\.venv\Scripts\python.exe src\librarian\retrieval_e5.py --sample
```
The first E5 run downloads weights from Hugging Face and caches them under `.cache/hf`. Current prototype is retrieval-only; it does not call an LLM API.

Build the curated local search index and run a query:

```powershell
.\.venv\Scripts\python.exe src\librarian\build_curated_corpus.py
.\.venv\Scripts\python.exe src\librarian\build_curated_index.py
.\.venv\Scripts\python.exe src\librarian\search_curated.py "Jak vybrat počet shluků v K-Means?"
```

The embedding matrix and model cache stay local under ignored `data/index/` and `.cache/` directories. See `docs/RETRIEVAL_PROTOTYPE.md` for corpus integrity and search details.

Run the retrieval-only Streamlit evidence browser:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-librarian.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8766
```

Only routes explicitly marked `verified` and a configured `streamlit_base_url` are rendered as clickable course links. Inferred paths appear as candidates until checked against the live course app.

See `docs/IMPLEMENTATION_PLAN.md`, `docs/GUARDRAILS.md`, `docs/LANGUAGE_SCOPE.md`, and `docs/RETRIEVAL_PROTOTYPE.md`.

For the algorithm/dataset reranking comparison, run
`.venv\Scripts\python.exe src\librarian\compare_constraints.py` and open
`http://localhost:8765/eval/quality_comparison.local.html` with the local workspace
HTTP server running. See `docs/CONSTRAINT_RERANKING.md` for results and limits.

Fresh-question evaluation on the repaired corpus: run `evaluate_quality.py`,
`score_quality.py`, and `render_quality_review.py` with `--set holdout_v1`.
The review is at `http://localhost:8765/eval/holdout_v1_review.local.html`.
See `docs/EVALUATION_HOLDOUT_V1.md` for provisional passage judgments and gaps.

The optional hybrid experiment is reproduced with `compare_hybrid.py` and reviewed
at `http://localhost:8765/eval/hybrid_comparison.local.html`. Production still uses
the candidate-and-reranker pipeline described below; equal-weight hybrid remains
experimental because it introduces regressions. See `docs/HYBRID_EXPERIMENT.md`.

The current app/CLI reranks E5 + TF-IDF candidates locally with a pinned multilingual
CrossEncoder. Download its public weights once with
`.venv\Scripts\python.exe src\librarian\prepare_reranker.py`; runtime is offline.
If unavailable, the app falls back to E5 with a visible warning. Explicit CLI modes
are `--mode rerank` (default), `--mode e5`, and experimental `--mode hybrid`.
Python API callers must pass `mode="rerank"`; its legacy default remains E5.
See `docs/RELIABILITY_RERANKER.md` and the full 25-query local review at
`http://localhost:8765/eval/reliability_comparison.local.html`.

Evidence availability now separates low-support matches from ordinary results.
For example, `kolik je hodin` shows a no-support message and collapsed weak matches.
Uncertain questions retain visible passages; E5 fallback is unassessed. The CLI
supports `--show-weak`. See `docs/ABSTENTION.md` and the 40-query local review at
`http://localhost:8765/eval/abstention_review.local.html` (`evaluate_abstention.py`).

The domain semantic layer separates multilingual aliases, abbreviations and typed
concept relations. Simple definition questions use versioned retrieval plans;
complex questions remain intact. See `docs/SEMANTIC_LAYER.md` and run
`src/librarian/compare_semantic.py` for the paired on/off excerpt review.

Every result now has “Otevřít zdroj”: browse static extracted context and download
the original snapshot file after manifest SHA-256 validation. No course page or
notebook is executed. See `docs/SOURCE_VIEWER.md` for limits and verification.

The first frozen cross-topic acceptance check remains **not accepted**. Its
historical PCA rejection and known English spam rationale have been repaired;
the known Polish soup case is now filtered by a narrow domain guard. New pancake
and multilingual retrieval failures still block acceptance.
See `docs/ACCEPTANCE_V1.md` and the
preserved original review at `http://localhost:8765/eval/acceptance_v1_review.local.html`.

Weak no-support matches now combine raw E5/reranker ranks only when every candidate
whole-query score is below .10. The support gate is unchanged. API
`ranking_strategy="reranker"` disables this fallback. See `docs/RANKING_FUSION.md` and
`http://localhost:8765/eval/ranking_fusion_v2_review.local.html`.

Source-adjacent headings now supply missing context for weak ordinary Streamlit
passages. Only an actual immediately preceding heading from static extraction is
used; original scores are retained, model weights/thresholds unchanged. The known
English PCA variance explanation is now first and supported (.021→.277).
Thirty full paired searches plus40 fixed-passage replays found no new supported
absent query; this is not independent human acceptance. Some PCA formulations
remain weak. See `docs/HEADING_CONTEXT.md` and all excerpts at
`http://localhost:8765/eval/heading_context_review.local.html`.

Explicit precision/recall priority questions now retain the original supported
winner and may add one missing error-cost explanation from the same candidate
pool. The known English spam query now shows the lost-work-email rationale second;
the context opens automatically and never supplies the original question's support
score. PL cost coverage still has gaps. See `docs/METRIC_CHOICE.md` and all paired
excerpts at `http://localhost:8765/eval/metric_choice_review.local.html`.

Evidence-v5 optionally uses a locally fitted logistic domain classifier only in
the original reranker's [.10,.20) grey band. Strong results and structural rules
keep their previous behavior; query vectors are reused and passage order/scores
are unchanged. The known Polish soup query becomes no_support. The new Polish
pancake query still incorrectly receives supported, and a valid feature-scaling
question remains hard rejected; no broad reliability claim is made. See
`docs/GREY_DOMAIN_GUARD.md` and the complete query/excerpt review at
`http://localhost:8765/eval/grey_domain_review.local.html`.

A broader 109-example domain model remains experimental: on 24 newly fixed
queries it rejects three unrelated results without rejecting a valid question,
but the known pancake query still fails the predeclared strong-result rule.
No production change was made. See `docs/DOMAIN_BREADTH.md` and full results at
`http://localhost:8765/eval/domain_breadth_review.local.html`.

Mixed nonsense plus ML terminology can still score highly: the schnitzel/tree
query is not fixed. Twelve contrastive searches show that removing source
metadata alone does not solve answerability. The UI now states this limit of
relevance scores explicitly. See `docs/MIXED_INTENT.md` and all paired scores and
excerpts at `http://localhost:8765/eval/mixed_intent_review.local.html`.

An independent local Qwen3-Reranker0.6B trial catches the known schnitzel query,
but misses all three new nonsense queries and downgrades one known valid query.
It is not integrated into production. See `docs/ANSWERABILITY_EXPERIMENT.md`,
all scores at `http://localhost:8765/eval/answerability_review.local.html`, and
the optional manual pair-label sheet at
`http://localhost:8765/eval/answerability_labels.local.html`.
