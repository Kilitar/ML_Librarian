> Current hosting target is the existing Streamlit course. Configure its server Secrets, not a second Librarian app. See [COURSE_INTEGRATION.md](COURSE_INTEGRATION.md).

# Streamlit presentation: no lecturer API key

## Goal and current state

A lecturer opens the hosted/preset Streamlit app, searches, consents to external
processing and clicks **Vygenerovat odpověď s citacemi**. No visitor key, model
field or local model installation. This user clarification supersedes previous
BYOK-only plan/guardrails. Retrieval tuning remains deferred, not accepted.

Groq Free Plan selected for the first integration; default model
`qwen/qwen3.8-27b`, configurable by operator. Multilingual answer quality and live
account availability remain UNVERIFIED. Existing quote/source validation remains.
When config is missing, the UI explicitly says generation is not configured and
disables the submit; search still works. A configured app is not yet a verified
hosted deployment: local runtime is http://localhost:8766/.

## One-time operator setup (not the lecturer)

1. Create/use a dedicated Groq **Free Plan** account and obtain an API key at
   https://console.groq.com/keys. Do not enable a paid billing plan for this demo.
2. In deployed Streamlit app Settings → Secrets, enter:

```toml
GROQ_API_KEY = "YOUR_REAL_KEY"
GROQ_MODEL = "qwen/qwen3.8-27b"
```

For local operation copy `.streamlit/secrets.example.toml` to the ignored
`.streamlit/secrets.toml` and fill it there; restart if needed. Alternatively set
server environment GROQ_API_KEY and optionally GROQ_MODEL. Secrets override env.
Never send a key in chat, commit it, put it into app code, or share it with the
lecturer. No key is currently configured in this workspace. No account has been
created, plan changed or external deployment performed by this implementation.

3. Try one supported course query and inspect the actual answer/citations. This
   live acceptance remains outstanding until operator configuration is present.

## Quota, provider and limits

Groq requests use fixed `https://api.groq.com/openai/v1/chat/completions`, JSON
mode, no tools, redirects, automatic retry or fallback to OpenAI/paid providers.
125 tests and Streamlit AppTest with mocked HTTP validate request contract and
visitor flow, not live multilingual quality. The existing explicit query/excerpt
consent is retained. No visitor key is stored in session state; server credentials
remain on server, without displaying/logging them.

API has no parameter that proves account billing is free. Using a paid Groq
account could incur charges: the operator must configure a Free Plan account.
Limits are organization-wide and may change. HTTP 429 displays quota exhaustion
and retains all evidence. Prompt limit 5 × 4 000 characters plus bounded output may
also exceed token-per-minute quota; no claim of unlimited/free guaranteed uptime.
Different character/token counts and shared classroom traffic matter.

Sources checked 2026-10-18:
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
- [API contract](https://console.groq.com/docs/api-reference)
- [Billing/account controls](https://console.groq.com/docs/billing-faqs)
- [Provider data handling](https://console.groq.com/docs/your-data)

Groq does not retain inference content by default, but reliability/abuse logs
may retain content up to 30 days subject to exceptions/settings. Do not describe
this as guaranteed zero retention. Source citation verification is not proof of
factual correctness or complete answer coverage.12 reserved questions stay unused.
