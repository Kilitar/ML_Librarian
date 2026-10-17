# Passage-level quality checkpoint — 2026-10-17

## Scope and reproducibility

Nine questions were fixed before retrieval: six previously unused topic/intent pairs
(two Czech, two English, two Polish; three conceptual and three practical), plus
three deliberately unanswerable questions. The existing production E5 index and
ranking were used unchanged. No source checkout, corpus, embedding, or UI change.

```powershell
.venv\Scripts\python.exe src\librarian\evaluate_quality.py
.venv\Scripts\python.exe src\librarian\score_quality.py
```

The first command loads the existing index and offline model cache, and writes
`eval/quality_results.local.json` (ignored; contains full excerpts). The second
checks the committed passage judgments against question/search hashes, corpus
fingerprint, passage IDs, order and text hashes before scoring. Judgments with
individual reasons live in `eval/quality_judgments.json`.

Reviewer: Codex, **provisional and not learner-approved**. Grade 2 means directly
useful evidence for the main requested concept or exact practical task; it may
need complementary passages for full coverage. Grade 1 is related/partial evidence
or a wrong dataset/algorithm. Grade 0 does not support the requested information.
This reviews evidence support, not the factual accuracy of every source claim.

## Result

| Query | Language / intent | First directly useful passage | Useful passages / 5 |
|---|---|---:|---:|
| Ridge, multicollinearity and alpha | CZ / concept | 1 | 2 |
| Diamond regression-tree exercise | CZ / practice | 2 | 1 |
| Preprocessing leakage inside CV | EN / concept | 3 | 2 |
| Lumbar logistic-regression exercise | EN / practice | 1 | 2 |
| DBSCAN core/border/noise | PL / concept | 2 | 2 |
| TF-IDF movie-sentiment exercise | PL / practice | 1 | 1 |

For the six answerable questions: Hit@5 **6/6**, MRR@5 **0.722**,
Precision@5 **10/30 = 0.333**, directly useful top-one **3/6**.
These are pool judgments over this retriever's top five, **not corpus-wide Recall@5**.
The small sample does not establish broad multilingual parity, full answer
coverage, or independent human validation. It is not comparable to the earlier
path-based scores. After inspection this set is consumed and is a regression /
development set; future tuning needs a new sealed held-out set for final evaluation.

## Concrete defects and next work

1. Practical requests lose exact constraints: diamond tree queries rank XGBoost,
   concrete trees and diamond linear regression; lumbar logistic queries include
   diabetes, trees and even a concrete homework copy-paste warning. Intent labels
   alone are too coarse. Develop algorithm/dataset matching on development queries.
2. Correct topics can still be incomplete passages: leakage explanations at ranks
   1–2 omit CV-fold isolation, and DBSCAN definitions start at rank 2. Preserve
   passage-level review instead of judging an entire file by its path.
3. Duplicate content from different files survives source diversification: the
   DBSCAN result contains the same family-comparison table twice. Investigate
   content-level diversification independently of source paths.
4. Out-of-scope questions returned unrelated excerpts in all three languages.
   Their top ranking scores were **0.832 / 0.819 / 0.801**. There is no abstention
   mechanism today; returning results is not a successful rejection. Scores are
   retrieval ordering signals, not probabilities of correctness. Do not derive a
   production threshold from these three examples.
5. One unrelated result contains raw HTML/CSS fragments from a Streamlit source.
   This is an extraction-quality issue, separate from the Markdown display fix.

BYOK answer synthesis remains deferred. Next bounded step: improve exact
algorithm/dataset matching on the development set, compare against the frozen
baseline, then validate on fresh questions before claiming improvement.
