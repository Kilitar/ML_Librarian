# Evaluation pilot (Oct 2026)

The pilot uses 12 authored queries: four concepts (k-NN scaling, choosing K-Means k, TF-IDF vs Bag of Words, PCA explained variance) in Czech, English, and Polish. Polish queries target Czech/English course evidence. Gold source paths are provisional labels and require learner review before a final claim.

For an apples-to-apples smoke evaluation, both TF-IDF and `multilingual-e5-small` were scored against the same deterministic 600-passage sample; Python comments and notebook code were excluded. Nine queries had at least one gold source path present in that sample. On only those nine:

| Retriever | Recall@5 | MRR@5 |
|---|---:|---:|
| TF-IDF | 0.67 | 0.50 |
| multilingual-e5-small | 1.00 | 0.69 |

This is a pilot signal, not a quality guarantee: 3 queries were excluded because their gold sources were absent from the sampled candidate set, gold paths are not yet human-validated, and page-level relevance is coarse. The full curated-corpus comparison is recorded in [EVALUATION_FULL.md](EVALUATION_FULL.md); its strict-path Recall@5 is lower and exposed mismatches in the provisional labels.

Raw top-five results and passage excerpts are local in the ignored file `eval/retrieval_prototype_results.json`.
