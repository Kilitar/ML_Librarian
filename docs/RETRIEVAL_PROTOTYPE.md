# Retrieval prototype notes

## Candidate

`intfloat/multilingual-e5-small` (MIT; model card lists 94 languages). Encoded locally using `passage:` and `query:` prefixes, normalized vectors, and CPU inference. No course text or query is sent to an embedding API.

## Current local search

The curated corpus has 4,196 chunks from 347 sources. Full indexing runs locally on CPU in roughly 2 minutes on this development machine. Nothing is sent to an embedding API. The versioned matrix and manifest are stored under ignored `data/index/` paths. Each manifest identifies the model, exact ordered corpus fingerprint, dimensions, and index filename; the search service refuses stale or unsafe index references. Rebuilds create a new fingerprinted matrix and only switch the manifest after the new matrix is complete, leaving the previous matrix available. Runtime model loading is restricted to the local cache, so query-time search does not contact Hugging Face.

Build the search index and try a query:

```powershell
.\.venv\Scripts\python.exe src\librarian\build_curated_corpus.py
.\.venv\Scripts\python.exe src\librarian\build_curated_index.py
.\.venv\Scripts\python.exe src\librarian\search_curated.py "Why should features be scaled before k-NN?"
```

`src/librarian/search.py` is the local retrieval interface intended for the standalone Streamlit UI. Results preserve chunk ID, source path, locator, provenance, and candidate Streamlit route; route metadata is explicitly marked as needing live verification. The search layer has no API credentials or write access to course files. It validates query length and result limit, and returns evidence only; it does not generate answers.

## Reproduce the initial 600-passage comparison

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-librarian.txt
.\.venv\Scripts\python.exe src\librarian\retrieval_e5.py --sample
```

The 600-passage result is only a pilot. The full curated-corpus comparison and its limitations are in `EVALUATION_FULL.md`.

## Limits / next work

- The current 12 expected source labels need human review; see `EVALUATION_FULL.md`.
- The local route map contains inferred Streamlit paths that need live verification.
- Search is retrieval-only; evaluate answer language and grounding separately when adding a free-tier LLM.
- PDF extraction artifacts remain in some original source text and can affect ranking.
