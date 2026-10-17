# Algorithm/dataset matching — 2026-10-17

## Behavior

The production retriever retains E5 semantic scores and its existing intent,
length and OCR priors. A bounded pool of 80 candidates is then reranked using
explicit algorithm/dataset aliases in CZ/EN/PL and common scikit-learn class names.
No corpus or embedding rebuild is needed. Source diversification remains unchanged.

Per requested entity category:

- A text match adds up to 0.03; a source-path/title-only match adds 0.02.
- For practical requests, explicit alternative source labels subtract 0.04 and
  alternative text labels subtract 0.02. Missing labels stay neutral.
- Practical text bonuses are diluted when a passage lists several alternatives,
  so a directory listing cannot win just by naming everything.
- Vectorizers, estimators, clustering algorithms and PCA are separate groups;
  TF-IDF with LogisticRegression is not a mismatch.
- Conceptual questions retain useful passages even if the source file has another
  algorithm in its name, e.g. DBSCAN definitions inside a K-Means presentation.

The controlled alias registry is deliberately limited. It does not parse negation,
fully understand multi-part requirements or certify that a named exercise is
actually taught by every excerpt. Multiple requested values are treated as
alternatives, not a requirement that every one appear. This is a soft prior, not
a filter or evidence-confidence score. Weights were developed on the reviewed
development set; no new held-out performance claim is made.

## Review actual results

```powershell
.venv\Scripts\python.exe src\librarian\compare_constraints.py
```

Open `http://localhost:8765/eval/quality_comparison.local.html` while the existing
workspace HTTP server is running. The report contains all nine exact questions,
copy buttons, old/new top-five results, scores, provenance and expandable full
excerpts. It is generated locally and ignored by Git, as is its JSON counterpart.
Source HTML is escaped. The report's plain excerpts aid comparison; the main
Streamlit app keeps Markdown/math rendering.

Both variants run against one loaded offline index. `match_constraints=False`
reproduces the previous production ranking, while the default enables matching.
All nine old top-five chunk-ID sequences were checked against the frozen prior
run and matched exactly. The report records current source and corpus hashes.
Historical `quality_judgments.json` remains unchanged; new results must not be
scored against old judgments without reviewing changed passages.

## Observed changes on development queries

| Query | Before | After |
|---|---|---|
| Diamond regression-tree exercise | XGBoost first, exact tree exercise second | Exact tree exercise first; tree/diamond tuning exercises second and third |
| Lumbar logistic-regression exercise | Lumbar first, diabetes second, exact assignment third | Exact lumbar assignment first; other lumbar logistic examples second–fourth |
| Movie sentiment with TF-IDF | Correct TF-IDF introduction first; partial vectorizer step third | Correct introduction first; full IMDb TF-IDF training assignment second |
| Ridge/multicollinearity | Useful first passage | Same five passage IDs/order |
| Preprocessing leakage and CV | Fold-isolation explanation third | Same five passage IDs/order |
| DBSCAN point definitions | Exact definition second | Same five passage IDs/order |
| Three absent/out-of-scope questions | Unrelated passages returned | Same five passage IDs/order; abstention still absent |

Residual defects remain visible: diamond-tree result 5 explains feature importance
rather than giving training instructions; the lumbar result 5 is only a metrics
exercise heading; sentiment results 3–5 include dataset context and preprocessing,
not TF-IDF classification. Entity matching does not prove passage completeness.
Duplicate content and source HTML extraction remain separate follow-ups.

## Verification and live app

Eight unit tests cover scoring integrity, multilingual aliases, exact versus wrong
algorithm/dataset, missing labels, comparisons, incidental mentions/catalogues,
and vectorizer/classifier compatibility. Local index comparisons completed for
all nine questions. Generated report checked for nine pairs / 90 cards and escaped
source HTML. Streamlit was restarted only for this workspace on port 8766; its
health endpoint returned `ok`. Learner comparison/visual acceptance is pending.

Next: learner reviews the linked comparison; then choose content diversification
or passage completeness as a separate bounded change. Final quality assessment
still needs fresh sealed questions and independent judgments.
