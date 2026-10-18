# Right-hand Librarian dock

Course host app.py calls render_dock() before nav.run(), giving every course page
the same common entrypoint. Native keyed st.container widgets are positioned by
scoped CSS: fixed launcher bottom-right, scrollable panel on the right, narrow
viewport rule for mobile. No iframe, JavaScript DOM mutation or browser storage.
The animation respects reduced-motion preferences. Existing full-page search and
lecturer documentation remain available; no lecturer layout redesign in this step.

@st.fragment limits ordinary dock widget reruns to its own UI, per the Streamlit
API. The open flag, submitted query, filters, returned passages, generated answer
and errors live in a non-widget session dictionary ml_dock_state. Widget cleanup
on close/page changes therefore cannot delete submitted results. Unsubmitted
form edits are not promised across closing/reopening; submit to retain them.
A full browser refresh/new session may lose all state. Sessions do not share
queries/answers; only loaded model resources are process-cached. Dock and embedded full-page search share the same cached index factory, avoiding duplicate neural model loads.

Closed dock imports no search/model code and prepares no data/weights. First
opening uses the same embedded.prepare_search setup as full-page search; loading
an index occurs only on search submission. No fitting/reindexing/training. Filters
are passed to the same retrieval backend, evidence gate and generated citation
validation remain unchanged. No-support/unassessed cannot generate; uncertain
answers stay qualified. Generation still needs operator Groq configuration.
There is no lecturer API key or model field. Failed/new searches clear old answers.

Functional validation: course AppTest closed lazy state, open, actualcd01search
with same5frozen IDs, navigation home→lecturer, close→home→reopen preserves query
and results. Instructor docs remain available with no second sidebar. Backend
unit suite129tests remains relevant. CSS desktop/mobile positioning, color,
contrast, touch targets and scrolling require the user's actual visual review;
AppTest is not a browser screenshot and does not validate CSS geometry.

Source APIs consulted:
- https://docs.streamlit.io/1.54.0/develop/api-reference/layout/st.container
- https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment

CSS targets only module-owned st-key classes. Future Streamlit frontend changes
may require styling adjustment; no global lesson layout CSS is modified.

Visual feedback fix: launcher moved to5rem above viewport bottom plus mobile safe-area inset; open panel bottom raised correspondingly. This leaves room for Streamlit Cloud bottom-right controls without hiding provider controls.
