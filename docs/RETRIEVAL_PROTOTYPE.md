# Retrieval prototype notes

## Candidate
`intfloat/multilingual-e5-small` (MIT; model card lists 94 languages). Encoded locally using `passage:` and `query:` prefixes, normalized vectors, and CPU inference. No course text or query is sent to an embedding API.

## Quick experiment
A deterministic 600-passage sample excluding Python comments and notebook code was encoded to a local `.npy` file (ignored by Git). This is a prototype, not a complete index or formal benchmark.

Queries included Czech and English k-NN scaling questions and a Polish question about choosing K-Means cluster count. On the Polish K-Means question, E5 ranked a relevant English exercise notebook first and K-Means theory in the top three. TF-IDF's top three were less relevant. This is an encouraging cross-language signal, not statistically reliable evidence of overall model superiority.

Embedding all 8,589 passages with the current CPU stack is estimated to take several minutes. Keep full indexing as an explicit offline step; profile batching or ONNX before deployment.

## Reproduce
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-librarian.txt
.\.venv\Scripts\python.exe src\librarian\retrieval_e5.py --sample
```

## Limits / next work
- Curate expected relevant passage IDs for CZ/EN/PL and compare Recall@5 and reciprocal rank on the same full corpus.
- Filter low-value UI labels/comments and fix PDF extraction artifacts.
- Profile full-index CPU time and memory.
- Evaluate answer language separately; E5 only retrieves.
