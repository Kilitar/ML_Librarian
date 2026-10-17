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
