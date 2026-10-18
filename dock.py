"""Session-scoped right dock; native Streamlit widgets, no iframe or browser storage."""
from pathlib import Path
import sys
import streamlit as st
ROOT=Path(__file__).resolve().parent
CSS="""<style>
.st-key-ml_librarian_launcher {position:fixed;right:1rem;bottom:calc(5rem + env(safe-area-inset-bottom, 0px));width:auto;z-index:990;}
.st-key-ml_librarian_dock {position:fixed;right:1rem;top:4rem;bottom:calc(8.8rem + env(safe-area-inset-bottom, 0px));width:min(440px,calc(100vw - 2rem));max-width:calc(100vw - 2rem);overflow-y:auto;overscroll-behavior:contain;padding:1rem;background:var(--st-background-color,var(--background-color,#0e1117));color:var(--st-text-color,var(--text-color,#fafafa));border:1px solid #80808066;border-radius:12px;box-shadow:0 8px 40px #0004;z-index:989;animation:mlDockIn .18s ease-out;}
@keyframes mlDockIn {from{transform:translateX(24px);opacity:0}to{transform:translateX(0);opacity:1}}
@media(max-width:600px){.st-key-ml_librarian_dock{right:.5rem;top:3.5rem;bottom:calc(8.5rem + env(safe-area-inset-bottom, 0px));width:calc(100vw - 1rem);max-width:calc(100vw - 1rem);}}
@media(prefers-reduced-motion:reduce){.st-key-ml_librarian_dock{animation:none}}
</style>"""


@st.cache_resource(show_spinner=False)
def get_index():
    from .embedded import get_search_index
    return get_search_index()


def toggle_dock():
    state=st.session_state['ml_dock_state']
    state['open']=not state['open']


@st.fragment
def render_dock():
    state=st.session_state.setdefault('ml_dock_state',{'open':False,'query':'','results':None,'answer':None,'error':None,'roles':[],'origins':[]})
    st.markdown(CSS,unsafe_allow_html=True)
    with st.container(key='ml_librarian_launcher'):
        st.button('Zavřít Librarian' if state['open'] else '📚 Librarian',key='ml_dock_toggle',on_click=toggle_dock)
    if not state['open']:return
    with st.container(key='ml_librarian_dock'):
        st.subheader('📚 Librarian')
        st.caption('Pomocník ke kurzu · CZ / EN / PL')
        from .embedded import prepare_search
        if not prepare_search():return
        from evidence_gate import assess_evidence
        from source_filters import SOURCE_ROLES,SOURCE_ORIGINS
        from snippet_format import format_snippet
        from demo_generation import demo_config,generate_demo_answer
        from answer_generation import GenerationError
        from course_links import render_course_link
        with st.form('ml_dock_search'):
            query=st.text_input('Dotaz ke kurzu',value=state['query'],max_chars=1000,key='ml_dock_query')
            with st.expander('Filtry zdrojů'):
                roles=st.multiselect('Skrýt typy',SOURCE_ROLES,default=state['roles'],key='ml_dock_roles')
                origins=st.multiselect('Skrýt původ',SOURCE_ORIGINS,default=state['origins'],key='ml_dock_origins')
            submitted=st.form_submit_button('Vyhledat zdroje',type='primary')
        if submitted:
            state.update(query=query,roles=list(roles),origins=list(origins),results=None,answer=None,error=None)
            if not query.strip():state['error']='Nejdřív napiš dotaz.'
            else:
                try:
                    with st.spinner('Hledám podklady…'):
                        state['results']=get_index().search(query,mode='rerank',limit=5,excluded_roles=roles,excluded_origins=origins)
                except Exception:state['error']='Vyhledávání se nezdařilo. Zkus to znovu.'
        if state['error']:st.warning(state['error'])
        if state['results'] is None:return
        results=state['results'];evidence=assess_evidence(results,state['query'])
        st.caption('Výsledky pro: '+state['query'])
        if evidence['status']!='supported':st.info('Opora je nejistá nebo nedostatečná; ověř nalezené pasáže.')
        config=demo_config(st.secrets)
        if evidence['status'] in ('supported','uncertain') and results:
            if not config['api_key']:st.caption('Generování zatím není nastavené provozovatelem.')
            consent=st.checkbox('Odeslat dotaz a níže uvedené úryvky službě Groq pro odpověď.',key='ml_dock_consent')
            if st.button('Odpovědět s citacemi',disabled=not config['api_key'] or not consent,key='ml_dock_generate'):
                state.update(answer=None,error=None)
                try:
                    with st.spinner('Připravuji odpověď…'):
                        state['answer']=generate_demo_answer(state['query'],results,evidence,config,consent=consent)
                except GenerationError as exc:state['error']=str(exc)
                except Exception:state['error']='Odpověď se nepodařila. Zdroje zůstávají dostupné.'
                if state['error']:st.warning(state['error'])
        answer=state['answer']
        if answer:
            if answer['status']=='partial':st.warning('Dílčí odpověď — ověř podklady.')
            elif answer['status']=='insufficient':st.info('Podklady neobsahují dostatečnou odpověď.')
            else:st.caption('Návrh odpovědi · ověř citace')
            for claim in answer['claims']:
                st.text(claim['text'])
                for citation in claim['citations']:
                    source=next(s for s in answer['sources'] if s['source_id']==citation['source_id'])
                    with st.expander(citation['source_id']+' · '+source['source_path']):
                        render_course_link(source)
                        st.text(citation['quote'])
            if answer['limitation']:st.text(answer['limitation'])
        st.caption('Nalezené zdroje · relevance není pravděpodobnost správnosti')
        for rank,row in enumerate(results,1):
            score=row['whole_query_score'] if row.get('ranking_policy')=='weak-fusion-v2' else row.get('ranking_score',row['score'])
            with st.expander(f'{rank}. {row["source_path"]} · {score:.3f}'):
                render_course_link(row)
                st.caption(str(row.get('source_role',''))+' · '+str(row.get('source_origin','')))
                st.markdown(format_snippet(row['text']),unsafe_allow_html=False)
                st.caption(str(row.get('locator'))+' · '+row['chunk_id'])
        st.caption('Stav se uchovává jen v této relaci. Obnovení stránky může relaci ukončit.')
