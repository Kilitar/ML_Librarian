# Contextual comparison ranking

The previous maximum-aspect coverage experiment failed regression/classification comparisons. This change adds a reviewed comparison axis to the semantic layer rather than treating any strong single-topic match as a good comparison.

Domain-v2 keeps the eight concepts and adds a `prediction_target` comparison axis shared by regression and classification. Reviewed Czech/Polish inflected names are aliases of the same concepts. Simple definition rewrites for those concepts remain disabled; only recognized comparison requests use the axis. The axis says what to compare, not what answer to return. No source IDs, canned answer text or source-specific boosts are used.

The reranker evaluates a context query such as “How do regression and classification differ in the type of prediction target?” alongside the original whole question and two aspect queries. It ranks using a fixed uncalibrated blend: `.50 * context + .25 * whole_question + .25 * sqrt(aspect1 * aspect2)`, followed by existing intent/constraint priors and deduplication. The geometric mean reduces the influence of a single strong side. We did not train weights or optimize these blend coefficients on the fresh formulations.

The original whole-question score is still separate. Context/aspect scores cannot directly create a supported decision. Evidence-v4 is unchanged. A strong contextual score is a relevance signal, not factual verification or a calibrated confidence estimate.

Production now defaults to `comparison_strategy='contextual'` for a recognized shared axis. The prior approved supervised/unsupervised pair retains its existing coverage route because it has no new axis. Other comparisons remain on baseline unless `comparison_experiment=True` is explicitly requested. `comparison_strategy='coverage'` reproduces the previous restricted production route; `comparison_tuning=False` disables comparison tuning. Fallback preserves the original question.

## Fixed paired check

12 questions were fixed before implementation: six development cases, three newly written formulations/orderings of known topics and three regressions. The final on/off run held code, questions and index fixed and stored their hashes. The diagnostic probe used known development passages only. This is not an independent unseen-topic benchmark.

Six regression/classification requests (three development, three new formulations) now have a direct explanation of continuous versus categorical targets first. Before, four first results were off-topic clustering and two were partial examples/logistic-regression context. All six now lead with `e81cca8e5f99452f636b`, a real corpus excerpt defining both output types. No ID is used by the search logic. Three new formulations test Czech reversal of concept order, English “differ from”, and Polish reversal/inflection; they remain correlated versions of one topic pair.

The other routes preserve useful behavior: label-based comparison remains uncertain and visible, ML definition supported, deep learning partial, and clock no_support. Overfitting/underfitting stays on the prior baseline in production. No overall Recall/Precision@5 or complete-answer accuracy is claimed. First-passage judgments are provisional Codex labels, with reasons and text hashes in `eval/contextual_judgments.json`.

Known limitation: later results can still be weak. The Polish development question's second result is a feature-scaling critique, despite the first result directly addressing the comparison. This checkpoint improves first evidence; it does not establish that the whole top five is useful. Source factual assertions were not audited here.

58 unit tests pass, including separate context/original scores, shared-axis validation, duplicate-concept rejection and asymmetric-evidence scoring. Eight actual Streamlit form submissions verify the three new formulations, house-price task choice, previous Polish labels behavior, clock, ML and deep learning. Returned ordering matches the frozen expected results.

## Review and reproduction

Run `compare_contextual.py` for the frozen questions in `eval/contextual_questions.json`. “Before” explicitly uses the previous coverage-only restricted production configuration; “after” uses the contextual experiment. The raw file predates promotion of the contextual default; hashes describe that frozen run. Do not overwrite existing reviewed raw output casually: a new result requires new review if hashes drift.

Run `render_contextual_review.py` to validate frozen raw/text hashes, render paired excerpts and append the local production AppTest results. Full review: `http://localhost:8765/eval/contextual_review.local.html`. Raw results/report are ignored by Git; questions, judgments, scripts and this explanation are tracked. New users of the checkout need the local corpus/model artifacts and frozen outputs before reproducing a labeled report.

Next: independent learner review and new topics outside this comparison pair; assess later-result usefulness separately. Expand the domain axes only after paired evidence supports them. Keep optional answer generation deferred until retrieval quality is accepted.
