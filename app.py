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
            relevance = result.get("ranking_score", result["score"])
            st.caption(f"Výsledek {rank} · relevance {relevance:.3f}")
        st.caption(f"Soubor: {result['source_path']}")

        with (st.container() if inline else st.expander("Zobrazit nalezený úryvek", expanded=(rank == 1))):
            st.markdown(format_snippet(result["text"]), unsafe_allow_html=False)
            language = result.get("language") or "neuvedeno"
            st.caption(
                f"Umístění: {result.get('locator') or 'neuvedeno'} · "
                f"Jazyk zdroje: {language} · typ: {source_role} · zdroj: {source_origin or 'neuveden'}"
            )
            st.caption(f"Chunk ID: {result['chunk_id']}")
            route = result.get("streamlit_route")
            if route and result.get("route_status") == "verified" and base_url:
                st.link_button("Otevřít stránku kurzu", urljoin(base_url.rstrip("/") + "/", route))
            elif route:
                st.caption(f"Kandidátní cesta ve Streamlitu: /{route} · čeká na ověření odkazu")


st.title("📚 ML Librarian")
st.caption("Lokální vyhledávání ve studijních materiálech · CZ / EN / PL")

st.info(
    "Toto je zatím režim **Evidence Search**: ukazuje nalezené úryvky a jejich původ. "
    "Odpověď generovaná LLM ještě není zapojena. Dotaz se ukládá pouze do paměti této relace."
)

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
    st.caption("Relevance je pořadové skóre, nikoli pravděpodobnost správnosti.")
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

st.divider()
st.caption("Index i embedding model běží lokálně. Vyhledávání neposílá obsah kurzu do externího API.")
