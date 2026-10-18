# Local source verification

Each result card includes “Otevřít zdroj”. The dialog shows its source path, the extracted source text and a selector for PDF pages, notebook cells or presentation text parts when the source has multiple records. It initially selects the exact matching locator, falling back to the first part if unmatched. A very long part is previewed up to 150, 000 characters; the original remains the complete source.

“Stáhnout původní soubor” serves immutable snapshot bytes, not an exported snippet. The source must occur in both `documents.jsonl` and the snapshot manifest. The download checks size and SHA-256 against the manifest and rejects paths outside the resolved snapshot. Downloads above 25 MiB are unavailable while extracted text remains readable. Original source code/notebooks are downloaded as files, never imported or executed. No course checkout writes, external requests or live course-page execution occur.

The dialog explicitly labels extracted text. Static text from notebooks/presentations is not an executed rendering; diagrams/math may reflect extraction limitations. SHA-256 verification applies to the original downloaded file, not a new factual check or independent re-extraction of the normalized text. Source facts may still be wrong. Existing unverified Streamlit routes remain candidates; this feature does not mark course URLs verified or change their base URL.

The extracted catalog is loaded lazily and cached by file mtime. Original bytes are verified on access. This feature adds no persistent query/key history, no embedding/index change and no answer-generation API. It works for main, supplementary and weak result cards; source filters still determine which cards exist.

Validation: 74 unit tests passed, including known-source/manifest requirements, matching original bytes, modified hashes, invalid/traversal/drive paths, resolved-path escape and download-size rejection. Three real AppTest search-and-open flows covered Markdown foundations, course introduction text and the Streamlit home presentation. Multi-part selector changes were exercised when available. The original course-summary PDF was read and hash-verified (23 extracted parts). These are functional checks, not visual acceptance of every source or validation of course facts.

Next: learner checks source-navigation usability; continue independent retrieval evaluation and demo preparation. Live course links still require separate runtime verification. Optional BYOK remains deferred.
