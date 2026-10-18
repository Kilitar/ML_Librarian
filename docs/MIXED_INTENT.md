# Mixed intent and answerability (2026-10-18)

**Unresolved retrieval failure.** The current relevance model can ignore an
absurd relation while matching the technical topic. This is not repaired by
removing source metadata, adding a dish blacklist, or changing a score threshold.

## Frozen contrastive diagnostic

`eval/mixed_intent_questions.json` contains four groups of three requests:
nonsense, a meaningful technical request, and a meaningful ML application to
food data. The user's schnitzel query was already inspected. The other eleven
formulations were fixed before running them. They are authored, correlated
examples, not an independent human test. Meaningful application does not imply
that a passage contains the exact application answer.

`evaluate_mixed_intent.py` runs all twelve real searches, preserves every returned
passage, and scores each query against its five raw bodies with the same pinned
crossencoder. This ablation removes source path, source title and supplemental
headings. It is not an independent answerability classifier. No new model, query
rewrite, trained weights, blacklist, ranking policy or evidence gate is deployed.

Three of four nonsense queries are incorrectly supported in production:

- Schnitzel for decision tree: production max .9795; text-only max .8074.
- Pouring soup into k-means: text-only max .6503, still supported.
- Adding flour to PCA: text-only max .6680, still supported.
- Oiling SVM: production no_support, but text-only max .2210. Naively replacing
  the gate score could even introduce a new false positive here.

All eight meaningful technical/application requests are supported by the current
gate and have text-only maxima >=.20. This does **not** establish complete answer
coverage or factual validity. No passage-level human judgments were added.
The metadata-removal hypothesis is rejected; text-only scoring cannot safely
replace or verify the current gate. The original acceptance remains not_accepted.

A cheap corpus-vocabulary diagnostic was also tried before this experiment:
`řízek` is absent, but valid Polish terms/inflections and English `leaking` are
absent too. A generic unknown-word veto would harm valid multilingual requests;
it was not implemented or used to change any result.

## User-facing change and checks

The app's relevance caption now explicitly says that high scores do not verify
coverage of the whole question or the question's meaningfulness. This is a
wording correction, **not a fix of the schnitzel query**. Its production status,
scores, five passages and order remain unchanged. Existing filters still apply.

106 existing unit tests pass. Two AppTest renders injected frozen real-result
sets (schnitzel and a valid food-clustering application), verified the caption,
retained IDs and all five source buttons. These are rendering checks, not new
end-to-end searches. Twelve actual searches are recorded separately above.
The verified Streamlit process was restarted after the UI change. Visual/human
readability review is separate from these checks.

## Reproduce and next step

Run `.venv/Scripts/python.exe src/librarian/evaluate_mixed_intent.py` from the
Librarian checkout. First run freezes raw results and tracked summary hashes of
code, questions, model config, normalized corpus and index manifest. It checks
these inputs again before writing. Later runs check the raw hash and render only.
Raw excerpts/HTML remain ignored local artifacts. All twelve queries, copy
buttons, all sixty excerpts and both scores:
<http://localhost:8765/eval/mixed_intent_review.local.html>.

Next work needs a separate query–passage answerability verifier or supervised
training with hard negatives that retain the correct topic but break the
requested relation. Evaluate it on separately frozen meaningful/nonsensical
minimal pairs and new applications, including valid food examples; do not call
this inspected set fresh again. Neither the current E5 domain classifier nor the
same relevance model rerun under another input format supplies that independent
signal. BYOK answer generation stays deferred.
