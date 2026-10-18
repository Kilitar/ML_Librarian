# Evidence availability / abstention — 2026-10-17

Current policy is evidence-v5: the optional learned grey-band domain guard is
described in `GREY_DOMAIN_GUARD.md`. Thresholds and structural exceptions below
remain; only ordinary uncertain results with a validated outside-domain signal
can become no_support. Historical evaluation figures below are preserved.

## User-visible behavior

For `kolik je hodin`, the app now says it did not find sufficient support in the
materials. It puts the five weak matches in a collapsed diagnostic expander rather
than presenting them as normal evidence. This is a search failure-to-support
message, not proof that information is absent from the entire corpus.

Uncertain questions keep visible result cards with an explicit notice and a
suggestion to clarify the topic/algorithm/dataset. Unassessed fallback results
also remain visible with a notice; unavailable reranking must not masquerade as
a negative evidence decision. Normal supported questions retain the existing UI.
The CLI follows the same decisions; `--show-weak` reveals low-support matches.
Raw `E5SearchIndex.search` remains diagnostic retrieval and still returns candidates.

## Policy evidence-v1

The gate uses the **original whole-query pair score**, before ordering priors or
the maximum across parameter-specific subquestions. Returned metadata distinguishes
`whole_query_score`, `passage_score` and `ranking_score`. A large source/intent bonus
or strong evidence for only one parameter cannot supply whole-query support.

- The pinned reranker revision must match and all required scores must be finite
  numbers in [0, 1]. Otherwise status is `unassessed`.
- Best whole-query score below 0.10: `no_support`.
- From 0.10 to below 0.20: `uncertain` (soft notice, visible results).
- At least 0.20: `supported` (passages may still be incomplete or factually wrong).
- A small explicit CZ/EN/PL list of context-free phrases such as “Jak to funguje?”
  and “Which is better?” requests clarification even if a generic passage scores
  highly. It is not a general language-understanding classifier.

These are version-specific heuristic operating points, not calibrated confidence
probabilities or a complete domain classifier. They were chosen using earlier
development cases (six unrelated queries below about 0.08 versus much stronger
course evidence), then frozen before new-query retrieval. The new set did not
trigger threshold changes. Scores from E5 or another reranker are never compared
to these thresholds. Fresh evaluations remain necessary if the scorer changes.

## Validation

Ran the 25 previous queries and 15 prewritten new queries, checking source/policy
hashes stayed unchanged during the run. New queries include clocks in CZ/EN/PL,
private information, weather, plumbing, short ML topics, a legitimate question about
training time, and three ambiguous phrases. Scope labels are Codex-authored; this
is a small local check, not independent human validation or universal performance.

| Group | Result |
|---|---|
| 25 regression queries | 25/25 expected statuses |
| 15 new queries | 14/15 expected statuses |
| All 12 absent/out-of-scope queries | 12 `no_support` |
| All 25 valid course queries | 24 `supported`, 1 `uncertain`, 0 `no_support` |
| Three ambiguous phrases | 3 `uncertain` |

The known mismatch is Polish `standaryzacja cech`, score about 0.120: a valid query
marked uncertain. Its results stay visible, so it is not a hard rejection. That
case is retained explicitly; no special topic whitelist or threshold retuning was
added after inspecting it. Training-time questions remain supported, so the clock
behavior is not a blanket ban on time-related words. `kolik je hodin` scored 0.0395.

Report with all 40 exact queries, decisions and expandable passages:
`http://localhost:8765/eval/abstention_review.local.html`.
Tracked summary: `eval/abstention_summary.json`. Full source excerpts remain local
and ignored. Reproduce with `evaluate_abstention.py`; it requires the local
`eval/reliability_comparison.local.json` to retain the 25 regression questions.

Thirty-one unit/integration tests passed. Real Streamlit AppTest submissions checked
the clock message and collapsed weak matches, ordinary PCA results, and visible
uncertain Polish results. The fallback/unknown-model and invalid-score gate paths
are tested. These checks do not substitute for learner visual acceptance.

## Next

Learner can re-submit the clock question after refreshing. Inspect the linked report
and the uncertain Polish case. A larger independent set should cover more in-domain
hard questions, mixed-intent queries and subtle near-domain unsupported questions.
Source factual quality and complete answer support remain separate targets; no LLM
answer generation or API calls were added. All inspected new cases now become
development/regression data.

## evidence-v2: explicit acronym questions

The learner query `Co znamená zkratka ML` exposed a false negative for the correct Machine Learning definition and false positives for MLM/MLE. Explicit acronym questions now match whole tokens and prioritize source-local expansions whose word initials match the requested acronym. Prose expansions supply structural support even when the model score is low, after the existing pinned-model/score checks. Fenced diagrams alone do not supply that override. This heuristic can still misread coincidental initials and does not validate source facts. The evidence-v1 40-query metrics are historical and have not been rerun for v2; the focused acronym check includes CZ/EN/PL ML, PCA, MLM, an unknown acronym, clock and the known uncertain Polish case. Full local excerpts: `eval/acronym_review.local.json` / `.html`.

## evidence-v3: bounded multilingual concept definitions

Simple CZ/EN/PL definitions of deep learning now use one canonical retrieval query. Related architecture passages from neural-network sources are prioritized by structural cues (networks, layers, explanatory prose) rather than treating neural networks as an exact synonym. This bounded route is always marked uncertain: the UI says the passages are related explanations, not a complete definition. Raw model scores remain unchanged, even if very low; the structural cue supplies related context only. Unknown-model/E5 validation still runs before this rule. Complex questions are left unchanged. The change is not general multilingual translation or a factual verifier. Eight AppTest submissions and 43 unit tests passed; historical 40-question metrics were not rerun. Full local review: `eval/concept_review.local.html`.

## evidence-v4: partial comparison evidence

Approved comparison retrieval may find strong passages for both sides despite weak whole-question relevance. Such results remain visible with an explicit uncertainty notice when each side has returned aspect evidence >= .20. This never supplies supported status by itself. Existing model/whole-score validation runs first; one missing side keeps ordinary low-support behavior. See `COMPARISON_TUNING.md`. Historical v1/v2/v3 metrics are not fresh v4 validation.
