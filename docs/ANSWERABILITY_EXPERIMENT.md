# Independent answerability trial (2026-10-18)

This is an offline experiment, not a production verifier. It uses a different
model from the existing mMARCO relevance scorer: Qwen3-Reranker-0.6B, pinned to
`e61197ed45024b0ed8a2d74b80b4d909f1255473`. The [official model card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
documents multilingual ranking, custom English instructions and scoring from
yes/no token logits. It does not establish answerability accuracy for this course.

## Fixed inputs and limits

- `config/answerability_experiment.json` fixes the instruction, .10 rejection
  threshold, CPU batch2 and 768-token budget before any Qwen predictions.
- `eval/answerability_questions.json` fixes nine new formulations: three
  nonsensical relations, three technical questions, three meaningful ML
  applications to food data, in CZ/EN/PL. Topic-correlated authored questions,
  not independent human or topic-level acceptance.
- Twelve prior mixed-intent requests and four ordinary/acronym controls reuse
  their stored five results. These sixteen are policy/scoring replays, not new
  end-to-end searches. Nine fresh requests perform actual full retrieval.
- The scorer sees the original question and passage body, plus a genuine
  adjacent heading when present. It does not see inferred source titles/paths.
  It computes a single forward pass's yes/no logits, never generates an answer,
  calls a paid API or gives the model tools. Query/documents remain local.
- The question is never truncated: >256 question tokens fails the diagnostic.
  Passage truncation is recorded explicitly. Any truncated returned passage
  disables the candidate downgrade for that question, rather than treating a
  partial view as proof that the answer is absent.
- Only ordinary supported results can become uncertain; no support upgrades,
  ordering/whole-score changes, acronym/comparison/semantic/related-only or
  ambiguity changes. This is a candidate rule, not deployed behavior.

Promotion criteria fixed in the config require repairing known schnitzel,
no supported fresh nonsense remaining, no meaningful supported downgrades in
fresh or known checks, and <=20 seconds extra scoring per question on this CPU.
Low verifier scores cannot prove that a question is meaningless. Neither model's
scores are calibrated probabilities of a correct answer.

## Local setup and reproduction

Only allowlisted tokenizer/config/license documentation and `model.safetensors`
are fetched into the ignored `.cache/hf`; no pickle weights or remote code.
The public 1.19GB safetensors download is checked against its published SHA256.
The model is loaded locally with `trust_remote_code=False`, token=False and
`local_files_only=True`. Production requirements/model cache stay optional;
normal Librarian does not import the experimental scorer.

Run `.venv/Scripts/python.exe src/librarian/cache_answerability_model.py` to
explicitly fetch the public model (HTTP transfer, Xet disabled) and verify its
published weight hash. Then run
`.venv/Scripts/python.exe src/librarian/evaluate_answerability.py` from the
Librarian checkout. First successful run freezes
all results, model-file hashes, input hashes, truncation flags and CPU timings.
Inputs are rehashed before output. Reruns verify raw SHA and render HTML only.
The ignored full report is served at
<http://localhost:8765/eval/answerability_review.local.html>.

The first retrieval attempt completed all nine searches but could not load the
model while its download was incomplete; it produced no verifier predictions or
frozen output. The stalled Hub transfer was stopped and retried over HTTP; no
question, instruction, threshold or promotion criterion was changed in response.

A second setup attempt loaded the weights but a complete-snapshot inventory
required unneeded Sentence Transformers files; it also produced no predictions.
The inventory was corrected to hash the explicitly cached files and model loading
was moved before retrieval. No semantic test setting changed. The final run
completed and its frozen raw/input/model hashes were verified.

## Measured result: not promoted

- Known schnitzel: supported→uncertain, max yes .0941, just below .10.
- All three fresh nonsense requests remain supported: sugar/random forest .8276,
  cheese/logistic regression .1684, tea/DBSCAN .7657. No new nonsense repair.
- All six fresh meaningful requests retain supported. However, known valid
  nearest-neighbour scale question `db08` changes supported→uncertain (.0397).
  This is a regression against the predeclared preservation criterion; without
  passage-level judgments it is not proof that either model's decision is right.
- Known soup/k-means and flour/PCA also remain supported. Oiling SVM gets a high
  Qwen score .9132, but remains no_support because the candidate never upgrades.
- One fresh application `aq09` has a truncated passage; downgrade is disabled.
- Extra five-passage scoring takes about4–9.21seconds per question; model startup
  about1.07seconds in the measured warm-cache run, separate from scoring.

The predeclared criteria fail: no production integration or default change.
This is a different model, but still trained for ranking. Its custom instruction
does not establish an independently reliable answerability signal. No prompt or
threshold was retuned to repair these now-inspected cases. Original retrieval
acceptance remains not_accepted and BYOK generation is deferred.

106 existing unit tests and compilation pass. Frozen render-only rerun preserves
raw SHA. Both reports returnHTTP200; app health returnsok. No AppTest/restart is
needed because no production or UI code changed in this checkpoint.

## Pair labels for the next supervised step

Run `.venv/Scripts/python.exe src/librarian/review_answerability.py`. It verifies
the frozen raw SHA and renders125 **unlabeled** query–passage pairs at
<http://localhost:8765/eval/answerability_labels.local.html>. Each has the actual
excerpt and provenance, optional scores hidden initially, and four choices:
whole-question coverage, partial/topic-only, irrelevant relation, unjudgeable.
The browser holds labels only in page memory until an explicit local JSON
download. Refresh discards them. No automatic upload, persistence, training or
human-approval claim. Exports bind query/text hashes, chunk ID and frozen raw SHA.

The page's selection, count, notes, export, untouched labels and provenance hash
were functionally checked with Node's VM and a simulated DOM. This is not a real
browser/download-save or visual review. No actual ratings were saved by that test.

Next: review passage coverage and build balanced supervised hard negatives that
retain the algorithm/topic but break the requested relation, alongside direct
positive passages and valid novel applications. Keep all inspected formulations
as development/regression data; freeze different topics/relations for validation
before fitting. More prompt/model swaps on this same set are not fresh evidence.
