# Full-corpus retrieval evaluation

## Scope

This offline comparison scores the same 12 authored questions (four topics in Czech, English, and Polish) against the full curated instructional-text corpus. The corpus contains 4, 196 chunks from 347 source files. It keeps course notes, PDF text, notebook markdown, and longer instructional Streamlit text; notebook code, Python comments/docstrings, and short UI literals are excluded. The source files and curation rules are recorded separately in the workspace.

The retrievers are word/character-independent TF-IDF (unigrams and bigrams) and `intfloat/multilingual-e5-small`, with E5's `query:` and `passage:` prefixes. Both rank the same candidates. Metrics are page-level Recall@5 and MRR@5: a result counts as relevant when its source path matches one of the provisional expected paths. Queries whose expected paths are absent from the corpus are excluded from aggregate metrics and reported explicitly.

## Interpretation

These are retrieval diagnostics, not a graded RAG answer-quality benchmark. The 12 questions cover four concepts and are not a representative test set. Expected source paths are human-authored but still need learner review; page-level matching can mark a passage relevant even when its particular excerpt does not answer the question. Inspect per-query top-five evidence before drawing conclusions, then add held-out questions and judge answer support before claiming answer quality.

## Current result (2026-10-17)

| Retriever | Recall@5 | MRR@5 | Questions with an expected path present |
|---|---:|---:|---:|
| TF-IDF | 0.50 | 0.27 | 12/12 |
| multilingual-e5-small | 0.67 | 0.51 | 12/12 |

The curated-corpus E5 result is lower than the 600-passage pilot. This is expected to be sensitive to the candidate set and current labels, and is not evidence that answer quality declined. A source audit found the expected PCA theory Markdown path used in all three PCA questions does not exist in the snapshot. In addition, top-ranked k-NN passages often come from the course's theory Markdown/notebook files rather than the originally specified Streamlit view paths. This makes strict source-path Recall@5 undercount useful evidence for those queries. Correct relevance labels and inspect the retrieved excerpts before comparing scores or presenting them as a benchmark.

Generated ranking details are in the ignored local file `eval/retrieval_curated_full_results.json`; run `src/librarian/evaluate_curated.py` to reproduce them with the local model cache.
