# Current decision — 2026-10-18

User clarified the goal: a lecturer opens the Streamlit presentation and can use
RAG without supplying a key or installing a model. This SUPERSEDES the earlier
BYOK-only interpretation below. Operator-configured Groq Free Plan is the primary
path. It uses shared organization quota; it is not an anonymous credential-free
provider API. No paid-provider fallback. See [setup](DEMO_GENERATION.md).
Historical notes below explain the previous assumption and are not current policy.

---

# LLM provider and credit isolation (checked 2026-10-17)

## Constraint from the project brief

Other people should be able to review the demo without spending the project owner's API quota. A provider key stored by the application would make every visitor's request consume that key's quota, even when the plan is free. Calling a provider “free tier” therefore does not make a shared server key cost-isolated.

## Recommended MVP modes

1. **Retrieval-only (default):** searches locally and displays evidence. No LLM request, provider key, or LLM usage is involved. This is the current running mode.
2. **Optional visitor-owned key (BYOK):** a visitor may enter their own provider key for one session. The application must not put it in source control, a shared secret, logs, files, or persistent session storage. It must disclose before submission that the visitor's query and selected course excerpts will be sent to that provider and charged against that visitor's quota. The key is passed only in memory for the request, then discarded. If the provider is unavailable or the user declines, retrieval-only still works.

Do not enable an owner-funded shared API key for a public or classroom demo under the current requirement. Do not claim universal free generation: free quotas, model availability, and data terms can change.

## Provider notes

| Provider | Current free usage / limits | Data handling relevant to this project | Assessment |
|---|---|---|---|
| Google Gemini Developer API | Google currently lists free input and output for some models, subject to account/model rate limits. | The general free-tier terms allow submitted content to be used to improve services and reviewed by people. The terms have a carve-out for users in the EEA, Switzerland, and UK: the paid-service data-use terms apply even to free quota. Since this project is in the Czech Republic, verify the applicable project terms at implementation time and show a clear provider disclosure. | Viable BYOK candidate; verify model quota and exact EEA treatment before activation. |
| GroqCloud | Free-plan limits exist and vary by model/account; exceeding them yields HTTP 429. Exact values are shown in the current account limits page. | Groq says it does not retain inference inputs/outputs by default, but may temporarily retain them up to 30 days for reliability or abuse investigations. An organization can enable Zero Data Retention. | Viable BYOK candidate; user must review its provider terms/data controls. |
| Hugging Face Inference Providers | Current pricing docs show no included monthly credits for Free accounts; credits are available to paid plans. | Billing is tied to the account/token routing each request. | Not a zero-cost default for an anonymous shared demo. |

## Decision before implementing the adapter

Keep retrieval-only as the reliable fallback and build generation as opt-in BYOK. Select the first provider only after checking its current multilingual quality, account/model quota, applicable data terms, and whether the intended reviewers are willing to supply their own key. No provider credential is needed for the local search UI or current workspace work.

## Official sources

- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API billing and tiers](https://ai.google.dev/gemini-api/docs/billing)
- [Gemini API Additional Terms, including EEA data terms](https://ai.google.dev/gemini-api/terms)
- [GroqCloud rate limits](https://console.groq.com/docs/rate-limits)
- [GroqCloud data retention and Zero Data Retention](https://console.groq.com/docs/your-data)
- [Hugging Face Inference Providers pricing](https://huggingface.co/docs/inference-providers/pricing)
