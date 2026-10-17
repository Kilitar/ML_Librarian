# Implementation plan

## Goal
A separate Streamlit RAG application over a versioned snapshot of the completed Data Science course. Index Czech and English course sources; support Czech, English, and Polish queries and answers; provide grounded answers and clickable source-page citations; allow retrieval when LLM is unavailable.

## Source boundary
`D:\Antigravity Projects\Data-Science` is read-only. All outputs and environments live here. First inventory an explicit allowlist; exclude Git, venvs, secrets, caches, logs, scratch, and unknown binaries. Snapshot selected files with relative paths, SHA-256, size, timestamp, type, topic, provenance, and candidate route. Never index live changing files.

## Ingestion
Read Markdown directly; extract PDF text page by page; notebook Markdown/code by cell; extract visible text from Python views statically without importing/executing. Preserve headings, formulas, code, page/cell locations, language, and provenance. Do not OCR unless inventory reveals a material text gap. Chunk at structural boundaries, assign stable IDs, and deduplicate while retaining source provenance. Produce normalized JSONL and exception report.

## Retrieval and generation
Implement TF-IDF then a multilingual embedding retriever using one interface. Evaluate cross-language retrieval. Add one free-tier LLM provider adapter. Send only query and top evidence; request answer in query language and citations by chunk ID; abstain when unsupported. Validate citation IDs and build URLs in app code. No paid fallback. On missing key, rate limit, or timeout, show retrieved evidence and explain generation is unavailable.

## UI and evaluation
Standalone Streamlit page with query, optional language choice, answer, evidence, source links, retrieval mode, and clear error state. Prepare development questions and a held-out set in CZ/EN/PL, including cross-language and unanswerable items. Learner confirms expected sources. Measure retrieval (recall@5, reciprocal rank) separately from answer correctness, citation support, and abstention. User manually checks readability/contrast, submit behavior, links, and error state; no routine screenshot loop.

## On-demand update
Explicit command compares hashes and creates a new snapshot/index version plus change report. Initial update may rebuild the whole index. Preserve previous versions. Never replace last known-good index before integrity checks pass.

## Timebox (~16 h estimate)
Preparation: isolation/inventory 1 h; extraction/corpus 2.5 h; chunking/provenance/routes 1.5 h; retrieval comparison 2 h. Sunday: LLM/fallback 2 h; UI 1.5 h; held-out evaluation 2 h; fixes/docs/demo 2.5 h; reserve 1 h. Trim advanced features before topic coverage.

## Agent and model budget
Luna low: bounded inventory, manifest, mechanical extraction, URL mapping, concise docs. Luna medium or Sol medium: coordinated implementation and UI. Sol medium: retrieval design, API failure handling, evaluation interpretation. Astra only for a specific unresolved high-impact decision or evidence conflict. Work serially with file ownership and concise handoffs. Track elapsed time, retries, tool calls, and API tokens where available; use the lightest configuration that meets acceptance criteria.

## User checkpoints
1. Review representative CZ/EN/PL passages, PDF page/notebook cell provenance, and original-vs-summary-vs-extension labels.
2. Review live UI: readability, contrast, submit behavior, correct citations and course-page links, API failure fallback.
3. Review representative and unanswerable answers for evidence support. User visual check is acceptance; automated checks do not substitute for it.

## Decisions to verify during inventory
Eligible file allowlist; deployed course URL base and route map; multilingual embedding candidate fitting available runtime; available provider free tier and data policy.
