> Superseded visitor setup: see [DEMO_GENERATION.md](DEMO_GENERATION.md). Current presentation uses server-configured Groq Free Plan; no lecturer key/model fields. OpenAI BYOK below documents the earlier prototype, not the current visitor flow. Citation validation remains in use.

# Answer prototype — 2026-10-18

User explicitly chose to stop extending retrieval tuning and move to the complete
RAG prototype. Evaluation is DEFERRED, not passed. Earlier acceptance remains
not_accepted; the 12 reserved questions remain unused. No ranking, model weights,
corpus, index, calibration threshold or evidence policy changed.

## Use

Open http://localhost:8766/, search normally, then use **Odpověď nad zdroji**.
Preview the exact query and source text under **Co se odešle modelu**. Enter a
model identifier available in your OpenAI API account (must support Chat
Completions JSON mode), enter your own key in the password field, consent to
sending these inputs using your quota, and submit **Vygenerovat odpověď s citacemi**.
No default model, account access, free quota or live quality claim is assumed.
Never paste a real key into chat, source files, logs or tests.

The form callback consumes/removes the key from session state before rendering
and clears its field; it is held only for the request, without caching or file
writes. No environment or shared owner key fallback. Query/answer remain only
in the current session. Search itself makes no generation API request.

## Behavior and limits

Only supported/uncertain retrieval may call the API; uncertain remains visibly
partial. No-support/unassessed abstain without sending. Model must independently
judge whole-question coverage, may return partial/insufficient, and has no tools.
Sources/question are explicitly untrusted data. This prompting and substring
validation do not prove entailment, factual correctness or injection immunity.
Known high-score nonsense failures in retrieval remain possible.

Each factual claim needs a valid supplied source ID and a contiguous verbatim
quote of at least 20 characters. Unknown IDs, invented quotes, uncited claims,
invalid JSON and incomplete output are rejected. The app builds source controls
from actual retrieval metadata, not model-generated URLs. Text renders as plain
text, preventing generated Markdown/HTML links. All original result cards remain.
A new search clears the old answer even if search fails. Provider errors also
clear the previous answer; generic errors never display provider bodies/headers.

Fixed endpoint https://api.openai.com/v1/chat/completions; no redirects, no tools,
no retry, 45s timeout, 5sources x4000 characters, 6claims, 1800completiontokens,
128KiB response cap,store=false. Preview marks source truncation. Character caps
are not token counts; provider may reject unsupported models or context sizes.
store=false does not claim zero provider retention; consult your provider terms.

Implementation checked against [official OpenAI Chat Completions documentation](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).

## Validation

122 unit tests passed, including fail-before-network consent/evidence checks,
quote/source integrity, bounded payload, uncertain downgrade, provider error
redaction and truncated-output rejection. Actual Streamlit AppTest uses frozen
retrieval results plus mocked provider: valid cited rendering, key removal,
API failure with sources retained, new-query invalidation and no-support block.
This is functional UI/contract verification, NOT a live paid API or quality test.
No real credential or paid API call was used. An initial mock target missed the imported callback; tests were corrected to intercept the HTTP transport. No successful live API response or live answer quality is verified. Next: use your API account
in the app for a small visible end-to-end review, then improve only failures
that matter to the full answer. Keep reserved acceptance questions unused until
candidate/protocol are fixed.
