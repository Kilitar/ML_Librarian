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
    submitted = st.form_submit_button("Vyhledat zdroje", type="primary")

if submitted:
    if not query.strip():
        st.warning("Nejdřív napiš dotaz.")
        st.session_state.pop("evidence_results", None)
    else:
        try:
            with st.spinner("Hledám relevantní pasáže v lokálním korpusu…"):
                index = get_search_index()
                st.session_state["evidence_results"] = index.search(query, limit=5)
                st.session_state["evidence_query"] = query
        except (FileNotFoundError, ValueError, OSError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("Lokální vyhledávání se nepodařilo spustit. Zkontroluj index a lokální model.")

results = st.session_state.get("evidence_results")
if results is not None:
    st.subheader("Nalezené zdroje")
    st.caption(f"Dotaz: {st.session_state.get('evidence_query', '')} · pořadí podle sémantické podobnosti")
    st.caption("📓 Cvičení / úkol · 🔎 Teorie / analýza · 🟨 ikona Coderslab označuje původní materiál z jeho PDF")
    routes_config = read_routes_config()
    base_url = routes_config.get("streamlit_base_url")

    for rank, result in enumerate(results, 1):
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
                st.caption(f"Výsledek {rank} · skóre {result['score']:.3f}")
            st.caption(f"Soubor: {result['source_path']}")

            with st.expander("Zobrazit nalezený úryvek", expanded=(rank == 1)):
                st.text(result["text"])
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

st.divider()
st.caption("Index i embedding model běží lokálně. Vyhledávání neposílá obsah kurzu do externího API.")
