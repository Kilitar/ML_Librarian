> Current deployment includes `deployment/runtime.zip` with the course module. Search auto-installs it after SHA validation; no external artifact URL/secret is required. Update exports with `--include-runtime`. Model weights still download on first use; Groq credentials affect only generated answers.

# Integrated course deployment — current target

User explicitly authorized minimal integration changes in Data-Science on
2026-10-18. This supersedes the read-only boundary ONLY for deploying Librarian;
other course content remains outside the work scope. Standalone cloud_app.py
is an optional development entrypoint, not the presentation deployment target.

## Architecture

Host repository: `Kilitar/Coderslab-DataScience`, existing `app.py` and Python 3.11.
Append group 36 with routes `/ml_librarian` and `/ml_librarian_lecturer`. Thin views
call the versioned `components/ml_librarian/embedded.py`. Host owns page config,
navigation, hosting URL and secrets. Librarian does not create a second sidebar
navigation in embedded mode. Lecturer view does not initialize neural models.
No training, fitting or reindexing runs inside either course view.

Implementation is developed in ML_Librarian and exported with:

```
python src/librarian/export_course_module.py --course-root PATH_TO_COURSE
```

The source-only export has a file SHA manifest and source commit/worktree status;
updates refuse to overwrite locally modified exported files. It includes modules,
config, instructor docs/notebooks and tracked summaries, not env/secrets/model
weights/runtime corpus/source originals/checkpoints. UTF8 text hashes normalize
CRLF toLF for cross-platform version control. Do not hand-edit exported files;
edit ML_Librarian then export again. Course-specific wrappers/nav stay in course.

## Data and model setup

Same runtime ZIP and SHA as deployment/artifacts.json. Install locally with the
validated deployment_bundle.install into course/components/ml_librarian, or set
RUNTIME_BUNDLE_URL/SHA256 in the EXISTING course app Streamlit Secrets. On first
access to the Librarian page the module fetches/verifies its artifact when no
local index exists. Other course pages do not fetch or load these resources.
GROQ_API_KEY/GROQ_MODEL also belong to course server Secrets; no lecturer key.

Models are pinned public E5 and MiniLM; first module initialization may download
weights, query-time execution is offline. Default cache is inside the exported
module's ignored.cache/hf. Optional server environment ML_LIBRARIAN_CACHE may
point to an existing compatible cache for local development. It is not needed
on Cloud. Course requires Librarian dependencies and Streamlit>=1.50; Python 3.11
stays unchanged. Linux 3.11 memory/startup/actual hosted generation still require
verification after the existing course deployment rebuilds.

Local integration does not update the immutable retrieval snapshot to include
these newly created app pages. Such reindexing is a separate explicit operation.
Current lecturer documentation is wired as-is; redesign remains deferred to
user review. Original source downloads remain unavailable with minimal artifact;
extracted source text browsing works.

## Publication

Publish both source repository and course integration checkpoint, then redeploy
or let existing Streamlit course rebuild from its current repo/branch/app.py.
Do NOT create a separate Librarian app as the target presentation. Existing course
URL and deployment credentials are still to be verified; no hosted-success claim
from a local smoke test. Course-controlled secrets and artifact hosting remain
operator prerequisites.
