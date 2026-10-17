# Retrieval quality checkpoint

Updated: 2026-10-17

## What the current app does

The Streamlit app is still an evidence search tool. It returns source excerpts and does not yet compose a natural-language answer. Raw excerpts can therefore feel fragmented even when retrieval finds the right topic; ranking and evidence quality must be reliable before optional LLM answer synthesis is added.

## Findings

- In the screenshot query “Kdy je dobré využít XGBoost?”, the top result was a 39-character PDF heading (“Examples of using XGBoost in practice 1”). A homework prompt ranked second and a theory passage third.
- Across the current 12-question diagnostic set and top five per question (60 passages), 4 passages were shorter than 180 characters. Seven PDF passages had a one-character-word ratio above 0.28, a useful flag for visibly spaced OCR text.
- The raw full-corpus E5 baseline is Recall@5 0.67 and MRR@5 0.51. The set covers four concepts in CZ/EN/PL, but its expected source paths are provisional and incomplete. For example, relevant k-NN theory appears in `02_Classification/theory/...`, while the current labels expect particular `views/...` paths. Strict path metrics therefore undercount useful passages.

## Experimental reranking

Ranking now keeps the original E5 score and applies small local adjustments:

- subtract 0.06 from chunks shorter than 120 characters;
- for PDF chunks only, subtract 0.06 when more than 35% of extracted word tokens are single characters;
- add 0.02 to theory/analysis for conceptual questions, or to exercise/example sources for explicit practice requests;
- prefer one result per source file before filling any remaining slots.

On the same 12 diagnostic prompts, this version produced Recall@5 0.75 and MRR@5 0.67, compared with 0.67 and 0.51 for raw E5. The XGBoost screenshot query now leads with a useful theory passage. Three practice-query smoke checks (CZ/EN/PL) returned exercise sources near the top. These are directional results on a small, hand-authored set, not a validated answer-quality claim.

## Next validation

1. Correct the current gold paths and judge relevance at the chunk level, including sources that are not Streamlit pages.
2. Add held-out questions across CZ/EN/PL and both conceptual and practical intents; do not tune against the held-out set.
3. Review short/OCR passages and distinguish extraction defects from ranking defects. Do not silently discard source evidence based on the current heuristic alone.
4. Once retrieved evidence is consistently useful, add optional cited answer synthesis as a separate evaluation target.

All experiments run locally against the Librarian snapshot. No course checkout files or corpus contents were changed.
