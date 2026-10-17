# Learner feedback: duplicates and broken diagrams — 2026-10-17

Reported query: `Kiedy należy zastosować metodę k-średnich`.
Reported diagram: old chunk `96ad59d81dea150585e1` from
`00_Prework/theory/03_data_prep_scikit_workflow.md`.

## Root causes and changes

- Source-level diversification did not detect identical excerpts copied between
  files. `diversify.py` now suppresses equal content after Unicode/whitespace
  normalization. Code fences preserve case and indentation in identity checks.
  Selection prefers distinct files, then distinct passages from the same file;
  it never restores a duplicate just to reach five results. Originals and their
  provenance remain in the corpus. Near-duplicates/paraphrases are not merged.
- Corpus construction collapsed repeated spaces in all text, including ASCII
  diagrams and Python code. `chunk_text.py` now treats fenced blocks atomically,
  preserves their internal whitespace and blank lines, and only normalizes prose.
  A fenced block may exceed the 1,100-character prose target to avoid splitting
  its fence. The embedding model's own token limit still applies.
- Added the Polish `k-średnich` algorithm alias for K-Means.

Rebuilt from existing Librarian normalized source records, without touching the
course checkout or immutable snapshot. Corpus now contains 4,189 chunks from
347 sources (previously 4,196). Rebuilt offline index fingerprint:
`11423d013eb8bd91` (prefix; full hash in the local index manifest).
Prior corpus and manifest: `logs/pre-format-fix/`; old versioned index remains.
Historical evaluation judgments and before/after reports describe the prior
corpus and must not be presented as current metrics.

## Verification

- Twelve unit tests passed, including fence whitespace/blank lines, oversized
  blocks, code indentation, cross-file duplicates, fallback deduplication,
  distinct numbers and the Polish alias.
- The exact reported diagram's complete fence was compared verbatim against
  `data/normalized/documents.jsonl` and found intact in the rebuilt corpus.
- Ran the exact reported query on the rebuilt production index: five results,
  five distinct normalized content keys. This confirms duplicate suppression,
  not that all five passages fully answer the question.
- Current local feedback report with all five excerpts and the intact diagram:
  `http://localhost:8765/eval/kmeans_feedback.local.html`.
  Local verification script: `logs/check_feedback.py` (generated, not tracked).
- Streamlit restarted for this workspace on port 8766. User must resubmit the
  query to replace stored session results. Visual acceptance remains with learner.

Reproduction: build curated corpus, build curated index with cached model,
then run `search_curated.py "Kiedy należy zastosować metodę k-średnich"`.
Source formatting fidelity and retrieval relevance remain separate checks.
