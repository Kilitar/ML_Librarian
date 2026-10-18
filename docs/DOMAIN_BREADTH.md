# Broader domain experiment — not promoted (2026-10-18)

The original 37 domain labels are supplemented by 72 authored synthetic queries:
36 course questions and 36 unrelated procedural questions, balanced across CZ,
EN and PL. These are domain labels, not labels of passage support. No visitor
queries or neural model updates are involved. The frozen v1 model is preserved.

Before fitting, `eval/domain_breadth_questions.json` fixes 24 new formulations
(12 course, 12 absent), model parameters and promotion criteria. Themes still
overlap training; this is not independent topic-level or human acceptance.
Known gd/gc examples are reported separately as 28 fixed-five-passage replays,
not fresh retrieval. Any exact historical training-query controls are marked
`training_query` in the raw output; none of the 24 fresh queries overlaps training.

The candidate adds rejection to the current production decision; it never
reverses the existing v1 rejection, upgrades evidence, or changes result order.
For ordinary questions with best whole-query score in [.10,.20), candidate
domain score <.50 rejects; for scores >=.20 it requires domain <.20. Ambiguity,
comparisons, semantic plans, acronym queries, related-only evidence and E5
fallback are protected. C10 balanced seed0 is unchanged from the original model.
Thresholds were fixed before fitting and were not changed after viewing outputs.

## Result and decision

- All 12 fresh course questions stay supported; no new valid rejection.
- Three fresh absent queries improve to no_support: `Jak připravit houskové
  knedlíky?`, `Jak nauczyć się pływać kraulem?`, `Jak odnowić kartę biblioteczną?`.
  The first and third were supported; swimming was uncertain. All 12 fresh
  absent queries end no_support. Domain classification at .50 is correct on
  these 24 formulations, which is not a general accuracy estimate.
- Known `Jak zrobić naleśniki?` remains supported. Domain score falls from
  .559 to .225, above the predeclared strong-result rejection threshold .20.
  The whole-query score remains .202711. This criterion fails, so the broader
  policy/model is **not promoted**. No threshold adjustment to fit pancakes.
- Known valid PL scale question gd11 remains no_support; domain score .870
  does not provide missing passage support. No known valid question is newly
  rejected. Original acceptance-v1 remains not_accepted; BYOK remains deferred.

Production search/app, v1 model, corpus and index are unchanged. Existing 106
unit tests pass. AppTest was not rerun because no runtime/UI code changed;
HTTP health and report availability were checked, not a browser visual review.

## Reproduce and inspect

Run `.venv/Scripts/python.exe src/librarian/evaluate_domain_breadth.py` in the
Librarian checkout. First run fits on cached pinned E5 vectors, performs 24
full searches and writes a safe numeric experimental model. It hashes inputs
before/after and rejects exact fresh/train overlap. Results/model are ignored
local files, not production artifacts. Tracked summary records their SHA256.
Subsequent runs verify the frozen raw hash and regenerate HTML only, without
fitting or overwriting results. Partial artifacts require a new experiment
version; do not delete frozen evidence to silently rerun the same trial.

Full questions, copy buttons, decisions, old/new domain scores and every excerpt:
<http://localhost:8765/eval/domain_breadth_review.local.html>.

Next: a distinct predeclared test of near-boundary procedural queries, including
valid ML procedures, before any further training. Compare a passage-aware
relevance check with the query-only classifier; more labels alone do not prove
the safety of rejecting strong matches. Keep these now-inspected 24 queries
as development/regression data. Multilingual support gaps remain a separate task.
