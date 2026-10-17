# Handoff

Updated: 2026-10-17. The course checkout is read-only; the immutable snapshot, extracted corpus, indexes, and all generated data live in this separate ML-Librarian workspace. No LLM API or user credentials are needed for the current retrieval work.

Completed: inventory/allowlist, source snapshot with hash manifest, extraction and route map, TF-IDF/E5 comparisons, instructional-text curation (4,196 chunks across 347 sources), full-corpus comparison, and a local E5 index/search service. Reproduce with `.venv\Scripts\python.exe src\librarian\build_curated_corpus.py`, `.venv\Scripts\python.exe src\librarian\build_curated_index.py`, then `.venv\Scripts\python.exe src\librarian\search_curated.py "your query"`. The index is versioned by a fingerprinted local file; its manifest switches only after a completed build. Runtime model loading is offline-only. Model cache and generated corpus/results/indexes are ignored by Git. Full evaluation details and caveats: `docs/EVALUATION_FULL.md`.

Current preview: retrieval-only Streamlit evidence browser at `http://127.0.0.1:8766`, bound to `127.0.0.1`. The app displays excerpts, provenance, chunk IDs, and candidate routes; it only makes a course link clickable after a route is marked verified and a base URL is configured.

Next: learner review of the UI and provisional expected source paths/top-five excerpts, especially k-NN and PCA; then use that feedback to make the benchmark labels useful and verify course links. Keep the 12 current questions diagnostic; add held-out questions for final evaluation. Then test the chosen free-tier LLM provider/fallback without exposing credentials.

Scope decisions: entire completed course; source corpus CZ/EN; user queries and same-language answers CZ/EN/PL. Polish demonstrates cross-lingual portability for Coderslab Poland, not an expected source language; citations should link to course Streamlit pages where routes are known; immutable versioned corpus with explicit on-demand update; free-tier LLM with retrieval-only fallback.
