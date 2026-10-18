# Fresh-question checkpoint after corpus repair — 2026-10-17

## Method

Nine new questions were fixed before retrieving their results on the repaired
4, 189-chunk index. Six course questions balance CZ/EN/PL and conceptual/practical
intent; three ask for private or live facts outside the corpus. Some subjects
overlap earlier course topics, so these are new question/task formulations, not
an entirely unseen domain benchmark. No ranking, alias, curation or index changes
were made during this run. Corpus fingerprint prefix: `11423d013eb8bd91`.

All 45 returned passages were reviewed by Codex with individual reasons and text
hashes in `eval/holdout_v1_judgments.json`. This is provisional model-authored
assessment, not independent human validation. Grade 2 means directly useful
evidence, potentially needing complementary passages; grade 1 is related but
insufficient; grade 0 does not support the request. Factual correctness of every
source statement was not audited. After review, this set becomes development /
regression data and must not be reused as a sealed test after tuning on it.

## Inspect and reproduce

Open `http://localhost:8765/eval/holdout_v1_review.local.html` for exact queries,
copy buttons, all five source paths/scores, provisional grades/reasons, and full
excerpts. The first excerpt is expanded. The local HTTP server must be running.
All source HTML is escaped; excerpts are shown verbatim for review. The report
does not change the main Streamlit UI.

```powershell
.venv\Scripts\python.exe src\librarian\evaluate_quality.py --set holdout_v1
.venv\Scripts\python.exe src\librarian\score_quality.py --set holdout_v1
.venv\Scripts\python.exe src\librarian\render_quality_review.py --set holdout_v1
```

Generated evidence/report files are ignored by Git. Questions and judgments are
tracked. Scoring and rendering reject mismatched questions, ranking helper hashes,
corpus fingerprint, passage IDs, order or text. Old `quality` artifacts remain
separate and describe the older corpus.

## Result

| Question / task | Language | First directly useful rank | Useful passages / 5 |
|---|---|---:|---:|
| RBF SVM: C, gamma and overfitting | CZ | 4 | 1 |
| Heart Random Forest exercise, precision tuning | CZ | 1 | 1 |
| Imbalanced accuracy and costly false negatives | EN | None | 0 |
| Diamond PCA exercise, scaling and variance | EN | 1 | 2 |
| Bagging vs boosting, training and bias/variance | PL | 1 | 5 |
| DBSCAN make_moons exercise and parameters | PL | 3 | 3 |

Answerable-question Hit@5 **5/6**, MRR@5 **0.597**, Precision@5 **12/30 = 0.400**,
directly useful first result **3/6**. These are retrieved-pool judgments, not
corpus-wide recall or a measure of complete/correct generated answers. The set
differs from earlier tests; the numbers do not establish a before/after change.

Three absent questions produced unrelated results and zero useful passages.
That is **not successful abstention**: the app still displays top matches.
Across these nine queries no repeated content keys survived selection.

## Evidence gaps and next bounded work

1. **Missed metrics evidence:** `recall_en` returns clustering passages and generic
   metrics fragments. The corpus does contain the accuracy imbalance pitfall:
   chunk `87de842ea65ce174a4a0`, `views/02_day_2_summary.py`, explicitly describes
   a majority-only predictor achieving 95% accuracy on a 95/5 split. Another chunk,
   `b16b3cd0df38d9ce7a7d`, `06_Final_Project/theory/01_machine_learning_course_summary.md`,
   includes imbalanced accuracy and recall's formula. Thus this is a retrieval
   miss, not evidence of absent topic coverage. These diagnostic finds were not
   added to the retrieved pool or scored as successful retrieval.
2. **Partial support:** SVM result 4 explains gamma/overfitting but the top five
   lack C's direction of effect. Topic matching alone does not ensure multi-part
   question coverage. The PCA task needs complementary passages too.
3. **Unmodeled dataset names:** The alias catalogue lacks heart and make_moons;
   heart RF is first but diamond RF appears second, while circles precede moons
   for DBSCAN. This exposes the controlled registry's limited coverage.

Recommended next experiment: compare lexical + E5 hybrid candidate retrieval on
the now-development metrics/SVM queries, rather than adding more ad hoc query
bonuses. Separately expand dataset aliases with tested CZ/EN/PL names for heart,
moons and circles. Freeze another question set before any final improvement claim.
BYOK synthesis remains deferred; adding an LLM would not repair these misses.

## Checks

Thirteen unit tests passed, including report escaping and stale-review rejection.
All nine offline searches completed on the unchanged index. The generated review
contains nine questions and 45 cards. Learner review remains pending.
