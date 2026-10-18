> Runtime delivery fix: course module ships its verified 7.8 MB `deployment/runtime.zip` directly. The external URL procedure below is optional legacy fallback. No manual data hosting or runtime URL secrets are needed for course search.

> Current target: integrate into the existing Streamlit course, not a new standalone deployment. See [COURSE_INTEGRATION.md](COURSE_INTEGRATION.md). The standalone procedure below remains a development alternative.

# Streamlit Community Cloud deployment

## Current evidence (2026-10-18)

Local app at http://localhost:8766/ is not a public deployment. Cloud entrypoint,
dependencies, private artifact packaging, lecturer documentation and notebooks
are prepared. No authenticated Cloud deployment or public URL is verified.
Browser automation timed out twice while obtaining app inventory; this is NOT
proof that the user is logged out. No provider key or hosting account configured.

## Deployment inputs

- GitHub repo `Kilitar/ML_Librarian`, branch `master`, entrypoint `cloud_app.py`.
- Root `requirements.txt` includes requirements-librarian.txt so Cloud discovers
  the dependencies. Local tests run on Python 3.14; choose 3.12 for a conservative
  Linux/Colab baseline, but Linux/Python 3.12 clean installation is still unverified.
- `deployment/runtime.local.zip`: extracted course documents, curated chunks,
  current index manifest and its 6.4 MB matrix. Built explicitly by
  `python src/librarian/deployment_bundle.py`. Current compressed size 7.8 MB.
- Original course files, secrets, model cache and experimental checkpoints are
  excluded. Original-download buttons therefore show unavailable originals;
  extracted source browsing is supported. Adjacent headings use documents.jsonl,
  which is included, so this context is not deliberately removed.
- Host the runtime artifact at an operator-controlled HTTPS URL accessible to
  the app. It can be signed/private but must remain usable for cold starts.
  Do not publish course data as a GitHub release without deciding its access.
  Its SHA is in deployment/artifacts.json. Rebuilding ZIPs may change their SHA;
  update this manifest and Cloud secret together.

## Operator steps

1. Ensure this checkpoint is pushed, log in at https://share.streamlit.io/ and
   choose Create app → existing app → repository/branch/entrypoint above.
2. In Advanced settings configure Python and these server Secrets:

```toml
RUNTIME_BUNDLE_URL = "https://YOUR_AUTHORIZED_ARTIFACT_LOCATION/runtime.local.zip"
RUNTIME_BUNDLE_SHA256 = "COPY_CURRENT_SHA_FROM_deployment/artifacts.json"
GROQ_API_KEY = "YOUR_DEDICATED_FREE_PLAN_KEY"
GROQ_MODEL = "qwen/qwen3.8-27b"
```

No real secret belongs in Git, notebooks, screenshots or chat. A template is in
.streamlit/secrets.example.toml. Lectors provide no API key/model. App does not
verify the provider account billing tier: use a free-only Groq account.

3. Deploy. cloud_app.py fetches an explicitly configured HTTPS artifact,
   validates outer SHA and member SHA/path/size allowlist BEFORE loading data.
   Then it downloads exact pinned public E5/reranker model revisions. Query-time
   models remain offline. No source code from an artifact is executed.
4. Verify cold start, model download, actual search, source filters, citations,
   quota failure, lecturer section and notebook download on the public URL.
   Compare actual full result IDs to the local app on a small set of known
   development queries. Do not use the 12 reserved acceptance questions here.
5. Check actual Cloud memory/latency. CPU torch/two neural models can exceed
   free-host resources; no free-host RAM/uptime guarantee has been measured.

If inputs are absent/invalid, cloud_app.py honestly displays setup status and
still offers lecturer docs; it does not claim working search or successful LLM.
The UI does not expose a private artifact URL. HTTP/errors are redacted.

## Lecturer notebooks / development bundle

Four notebooks under notebooks/ use actual project code/data, default heavy
steps off. They can be downloaded directly from Pro lektora or opened through
Colab GitHub links after publication. Those links require repository access.
An alternative is Colab File → Upload notebook. Colab login/upload/GPU execution
are not verified by local cell execution.

`python src/librarian/deployment_bundle.py --development` creates a separate
explicit allowlist of 6 development JSON files: 276 annotated pairs, 58 original
training rows, v1/v2 scored passages and v1 retrieval/notes. Size~194 KB. No
keys/cache/checkpoints/reservedtestqueries. It is for instructor analysis, not
runtime inference. Provide runtime and development ZIPs privately to authorized
lecturers; notebook imports check the exact SHA and member allowlist from
`deployment/artifacts.json`. Never bypass hash errors to load a different corpus.

Local notebook validation executed 23 code cells across 4 notebooks with real data;
neural search/training disabled. 129 unit tests pass (including bundle integrity
and unsafe member rejection). Streamlit AppTest checked 7 lecturer sections,
4 downloads/4 Colab links, summaries/code and cloud missing-config page. These are
local checks, not live public hosting or Colab UI tests.

## Official references

- [Deploy repository and configure secrets/Python](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Dependency file discovery](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

No public deployment URL should be reported until the final hosted smoke tests
have actually succeeded.
