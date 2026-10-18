from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urljoin

import streamlit as st

ROOT = Path(__file__).resolve().parent
CL_LOGO = ROOT / "data" / "Icons" / "codesrlab_logo_square.png"
sys.path.insert(0, str(ROOT / "src" / "librarian"))
from search import E5SearchIndex  # noqa: E402
from snippet_format import format_snippet  # noqa: E402
from evidence_gate import assess_evidence  # noqa: E402
from result_presentation import partition_results  # noqa: E402
from source_filters import SOURCE_ROLES, SOURCE_ORIGINS  # noqa: E402
from source_viewer import SourceCatalog, DOCUMENTS, initial_part  # noqa: E402
from answer_generation import prepare_context, GenerationError  # noqa: E402
from demo_generation import demo_config, generate_demo_answer  # noqa: E402


if not globals().get("LIBRARIAN_EMBEDDED", False):
    st.set_page_config(page_title="ML Librarian · evidence search", page_icon="📚", layout="wide")


@st.cache_resource(show_spinner=False)
def get_search_index() -> E5SearchIndex:
    return E5SearchIndex.load()


def read_routes_config() -> dict:
    path = ROOT / "config" / "streamlit_routes.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"streamlit_base_url": None}


@st.cache_resource(show_spinner=False)
def get_source_catalog(modified_ns):
    return SourceCatalog()


@st.dialog("Zdrojový materiál", width="large")
def show_source(result):
    st.caption(result['source_path'])
    try:
        catalog=get_source_catalog(DOCUMENTS.stat().st_mtime_ns)
        parts=catalog.parts(result['source_path'])
    except (OSError,ValueError):
        st.warning("Extrahovaný text zdroje není dostupný.")
        return
    try:
        original=catalog.original(result['source_path'])
        st.download_button("Stáhnout původní soubor", data=original,
                           file_name=Path(result['source_path']).name,
                           key='download_'+result['chunk_id'])
        st.caption("Původní soubor z lokálního snapshotu · SHA-256 ověřeno podle manifestu.")
    except (OSError,ValueError):
        st.warning("Původní soubor se nepodařilo ověřit pro stažení. Extrahovaný text je dostupný níže.")
    selected=initial_part(parts,result.get('locator'))
    if len(parts)>1:
        selected=st.selectbox("Část zdroje",range(len(parts)),index=selected,
                              format_func=lambda i: f"{i+1}. {parts[i].get('locator','document')}",
                              key='part_'+result['chunk_id'])
    st.caption("Extrahovaný text · "+str(parts[selected].get('locator','document'))+
               " · notebooky a prezentace obsahují staticky vytažený text, nikoli spuštěný výstup.")
    text=parts[selected]['text']
    if len(text)>150000:
        st.info("Náhled je zkrácený; celý obsah najdeš v původním souboru.")
    st.markdown(format_snippet(text[:150000]),unsafe_allow_html=False)


def source_role_badge(role: str) -> tuple[str, str]:
    badges = {
        "Teorie / analýza": ("🔎 Teorie / analýza", "violet"),
        "Cvičení / úkol": ("📓 Cvičení / úkol", "green"),
        "Příklad / implementace": ("🛠️ Příklad / implementace", "blue"),
        "Shrnutí / přehled": ("📋 Shrnutí / přehled", "yellow"),
        "Studijní materiál": ("📚 Studijní materiál", "gray"),
    }
    return badges.get(role, (f"📚 {role}", "gray"))


def render_result(rank, result, base_url, *, inline=False):
    source_role = result.get("source_role", "Studijní materiál")
    source_origin = result.get("source_origin")
    source_origin_icon = result.get("source_origin_icon", "📚")
    badge_label, badge_color = source_role_badge(source_role)
    with st.container(border=True):
        origin_col, role_col, rank_col = st.columns([0.29, 0.45, 0.26], vertical_alignment="center")
        with origin_col:
            if source_origin == "Coderslab PDF" and CL_LOGO.is_file():
                logo_col, label_col = st.columns([0.25, 0.75], vertical_alignment="center")
                logo_col.image(str(CL_LOGO), width=30)
                label_col.markdown("**Coderslab PDF**")
            else:
                st.markdown(f"{source_origin_icon} **{source_origin or 'Původ neuveden'}**")
        with role_col:
            st.badge(badge_label, color=badge_color)
        with rank_col:
            # RRF rank votes are near one even for irrelevant matches. Keep
            # displayed relevance low when all original model scores are low.
            relevance = (result['whole_query_score'] if result.get('ranking_policy') == 'weak-fusion-v2'
                         else result.get("ranking_score", result["score"]))
            st.caption(f"Výsledek {rank} · relevance {relevance:.3f}")
        st.caption(f"Soubor: {result['source_path']}")

        with (st.container() if inline else st.expander("Zobrazit nalezený úryvek", expanded=(rank == 1 or result.get('metric_choice_context', False)))):
            if result.get('metric_choice_context'):
                label = 'falešné poplachy (FP)' if result['metric_choice_plan']['error_code']=='FP' else 'přehlédnuté pozitivní případy (FN)'
                st.caption('Doplňující kontext k volbě metriky: '+label)
            if result.get('heading_context'):
                heading = result['heading_context']
                st.caption(f"Nadpis ve zdroji: {heading['text'].lstrip('# ').strip()} · {heading['locator']}")
            st.markdown(format_snippet(result["text"]), unsafe_allow_html=False)
            language = result.get("language") or "neuvedeno"
            st.caption(
                f"Umístění: {result.get('locator') or 'neuvedeno'} · "
                f"Jazyk zdroje: {language} · typ: {source_role} · zdroj: {source_origin or 'neuveden'}"
            )
            st.caption(f"Chunk ID: {result['chunk_id']}")
            if st.button("Otevřít zdroj",key='source_'+result['chunk_id']):
                show_source(result)
            route = result.get("streamlit_route")
            if route and result.get("route_status") == "verified" and base_url:
                st.link_button("Otevřít stránku kurzu", urljoin(base_url.rstrip("/") + "/", route))
            elif route:
                st.caption(f"Kandidátní cesta ve Streamlitu: /{route} · čeká na ověření odkazu")


view = ("Pro lektora" if globals().get("LIBRARIAN_SECTION")=="lecturer" else "Vyhledávání a odpovědi") if globals().get("LIBRARIAN_EMBEDDED", False) else st.sidebar.radio("Sekce", ["Vyhledávání a odpovědi", "Pro lektora"], key="app_section")
if view == "Pro lektora":
    from lecturer_view import render_lecturer
    render_lecturer()
    st.stop()

st.title("📚 ML Librarian")
st.caption("Lokální vyhledávání ve studijních materiálech · CZ / EN / PL")

st.info("Vyhledávání běží lokálně. Volitelný prototyp odpovědi s citacemi najdeš pod nalezenými zdroji. "
        "Dotazy a odpovědi se uchovávají pouze v paměti této relace.")


def request_answer():
    # Provider credential is server-only; never part of session/widget state.
    st.session_state.pop("generated_answer", None)
    st.session_state.pop("generation_error", None)
    try:
        rows = st.session_state.get("evidence_results", [])
        question = st.session_state.get("evidence_query", "")
        answer = generate_demo_answer(question, rows, assess_evidence(rows, question), demo_config(st.secrets),
            consent=st.session_state.get("llm_consent", False))
        st.session_state["generated_answer"] = answer
    except GenerationError as exc:
        st.session_state["generation_error"] = str(exc)
    except Exception:
        st.session_state["generation_error"] = "Generování se nezdařilo. Nalezené zdroje jsou stále dostupné."


with st.form("evidence_search", clear_on_submit=False):
    query = st.text_input(
        "Na co se chceš zeptat?",
        placeholder="Např. Why do we standardize features before k-NN?",
        max_chars=1000,
        help="Zadej dotaz česky, anglicky nebo polsky.",
    )
    with st.expander("Filtry zdrojů", expanded=False):
        hidden_roles = st.multiselect("Skrýt typy materiálu", SOURCE_ROLES, key="hidden_roles")
        hidden_origins = st.multiselect("Skrýt původ zdroje", SOURCE_ORIGINS, key="hidden_origins")
        st.caption("Například skryj cvičení nebo Coderslab PDF. Filtry se použijí po kliknutí na Vyhledat zdroje.")
    submitted = st.form_submit_button("Vyhledat zdroje", type="primary")

if submitted:
    st.session_state.pop("generated_answer", None)
    st.session_state.pop("generation_error", None)
    st.session_state.pop("evidence_results", None)
    if not query.strip():
        st.warning("Nejdřív napiš dotaz.")
        st.session_state.pop("evidence_results", None)
    else:
        try:
            with st.spinner("Hledám relevantní pasáže v lokálním korpusu…"):
                index = get_search_index()
                st.session_state["evidence_results"] = index.search(query, limit=5, mode="rerank",
                                                                  excluded_roles=hidden_roles, excluded_origins=hidden_origins)
                st.session_state["evidence_query"] = query
                st.session_state["evidence_filters"] = list(hidden_roles) + list(hidden_origins)
        except (FileNotFoundError, ValueError, OSError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("Lokální vyhledávání se nepodařilo spustit. Zkontroluj index a lokální model.")

results = st.session_state.get("evidence_results")
if results is not None:
    evidence = assess_evidence(results, st.session_state.get("evidence_query", ""))
    st.subheader("Výsledek vyhledávání" if evidence["status"] == "no_support" else "Nalezené zdroje")
    if evidence["status"] == "no_support":
        if st.session_state.get("evidence_filters"):
            st.info("Ve vybraných skupinách jsem nenašel dostatečnou oporu pro tento dotaz. Zkus povolit další skupiny nebo upřesnit otázku.")
        else:
            st.info("V materiálech jsem nenašel dostatečnou oporu pro tento dotaz. Zkus otázku ke kurzu Data Science / Machine Learning nebo upřesni téma.")
    elif evidence["status"] == "uncertain":
        if evidence.get("reason") == "comparison_partial_evidence":
            st.info("Našel jsem dílčí podklady k oběma částem otázky. Opora pro celé srovnání zůstává nejistá; ověř souvislost v úryvcích níže.")
        elif evidence.get("reason") == "related_concept_evidence":
            st.info("Našel jsem související výklad neuronových sítí a jejich vrstev. Tyto pasáže nejsou úplnou definicí hlubokého učení.")
        else:
            st.info("Opora v nalezených materiálech je nejistá. Níže jsou orientační pasáže; můžeš upřesnit téma, algoritmus nebo dataset.")
    elif evidence["status"] == "unassessed":
        st.info("Oporu dotazu se nepodařilo ověřit. Níže jsou základní podobné pasáže.")
    if results and results[0].get("retrieval_warning"):
        st.warning(results[0]["retrieval_warning"])
    st.caption(
        f"Dotaz: {st.session_state.get('evidence_query', '')} · pořadí podle relevance úryvku a záměru dotazu"
    )
    st.caption("📓 Cvičení / úkol · 🔎 Teorie / analýza · 🟨 ikona Coderslab označuje původní materiál z jeho PDF")
    st.caption(
        "Relevance hodnotí tematickou shodu. Ani vysoké skóre neověřuje, "
        "že úryvek odpovídá na celou otázku nebo že je otázka smysluplná."
    )
    active_filters = st.session_state.get("evidence_filters", [])
    if active_filters:
        st.caption("Skryté skupiny: " + " · ".join(active_filters))
    routes_config = read_routes_config()
    base_url = routes_config.get("streamlit_base_url")

    primary, additional = partition_results(results, evidence["status"])
    evidence_container = st.expander("Zobrazit slabé shody (nemusejí odpovídat na dotaz)", expanded=False) if evidence["status"] == "no_support" else st.container()
    with evidence_container:
        for rank, result in primary:
            render_result(rank, result, base_url, inline=evidence["status"] == "no_support")
    if additional:
        st.caption("Další shody mohou doplňovat kontext, ale nemusí přímo vysvětlovat celé srovnání.")
        st.caption("Čísla výsledků zachovávají původní pořadí vyhledávání.")
        with st.expander(f"Zobrazit další shody ({len(additional)})", expanded=False):
            for rank, result in additional:
                render_result(rank, result, base_url, inline=True)

    st.subheader("Odpověď nad zdroji · prototyp")
    st.caption("Citace ověřujeme proti textu úryvků. Samotná přítomnost citace nezaručuje správnost tvrzení; opora retrievalu má známá omezení.")
    if evidence["status"] in ("supported", "uncertain") and results:
        if evidence["status"] == "uncertain":
            st.warning("Opora je nejistá. Případná odpověď bude označena jako dílčí a je potřeba ji zkontrolovat.")
        with st.expander("Co se odešle modelu", expanded=False):
            context = prepare_context(st.session_state["evidence_query"], results, evidence)
            st.write(context["question"])
            for source in context["sources"]:
                st.caption(source["source_id"]+" · "+source["source_path"])
                st.text(source["text"])
                if source["truncated"]: st.caption("Úryvek pro model je zkrácen na 4000 znaků.")
        configured = bool(demo_config(st.secrets)["api_key"])
        if not configured:
            st.info("Generování prezentace ještě není nakonfigurované provozovatelem. Nalezené zdroje můžeš prohlížet už teď.")
        with st.form("answer_request", clear_on_submit=True):
            st.caption("Prezentace používá Groq. API klíč ani výběr modelu nejsou potřeba. Při vyčerpání limitu zůstává dostupné vyhledávání.")
            st.checkbox("Souhlasím s odesláním dotazu a výše uvedených úryvků službě Groq pro vytvoření odpovědi.", key="llm_consent")
            st.form_submit_button("Vygenerovat odpověď s citacemi", on_click=request_answer, disabled=not configured)

    else:
        st.info("Bez ověřené opory se generování nespouští. Upřesni otázku nebo prohlédni nalezené pasáže.")
    if st.session_state.get("generation_error"):
        st.warning(st.session_state["generation_error"])
    answer = st.session_state.get("generated_answer")
    if answer:
        if answer["status"] == "insufficient": st.info("Model v úryvcích nenašel dostatečnou odpověď.")
        elif answer["status"] == "partial": st.warning("Dílčí odpověď — podklady nepokrývají spolehlivě celou otázku.")
        else: st.caption("Návrh odpovědi z nalezených podkladů · ověř citace")
        sources = {source["source_id"]: source for source in answer["sources"]}
        for i, claim in enumerate(answer["claims"], 1):
            # Plain text prevents generated links/HTML from becoming actionable UI.
            st.text(claim["text"])
            for j, citation in enumerate(claim["citations"], 1):
                source = sources[citation["source_id"]]
                with st.expander(citation["source_id"]+" · "+source["source_path"]+" · "+str(source["locator"])):
                    st.text(citation["quote"])
                    match = next(r for r in results if r["chunk_id"] == source["chunk_id"])
                    if st.button("Otevřít citovaný zdroj", key=f"citation_{i}_{j}"): show_source(match)
        if answer["limitation"]: st.text(answer["limitation"])

st.divider()
st.caption("Index i vyhledávání běží lokálně. Pouze výslovně vyžádané generování odešle dotaz a nejvýše 5 úryvků službě Groq.")
