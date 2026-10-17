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

See `docs/IMPLEMENTATION_PLAN.md`, `docs/GUARDRAILS.md`, `docs/LANGUAGE_SCOPE.md`, and `docs/RETRIEVAL_PROTOTYPE.md`.
