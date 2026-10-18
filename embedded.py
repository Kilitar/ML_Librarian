"""Course-page entrypoint: host owns page configuration/navigation and secrets."""
import os
import runpy
import sys
from pathlib import Path
import streamlit as st
ROOT=Path(__file__).resolve().parent


def render(section='search'):
    if section not in ('search','lecturer'):raise ValueError('Unknown Librarian section')
    sys.path.insert(0,str(ROOT/'src/librarian'))
    if section=='lecturer':
        from lecturer_view import render_lecturer
        render_lecturer()
        return
    if not prepare_search():return
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__',init_globals={
        'LIBRARIAN_EMBEDDED':True,'LIBRARIAN_SECTION':section,'LIBRARIAN_INDEX_FACTORY':get_search_index})


def prepare_search():
    sys.path.insert(0,str(ROOT/"src/librarian"))
    if not (ROOT/'data/index/multilingual_e5_curated.json').exists():
        try:
            with st.spinner('Připravuji data Librarianu…'):
                from deployment_bundle import provision_runtime
                provision_runtime(ROOT,st.secrets)
        except Exception:
            st.error('Data Librarianu se nepodařilo připravit. Zkus obnovit stránku; provozovatel může zkontrolovat integritu nasazení.')
            return False
    try:
        ensure_models()
    except Exception:
        st.error('Modely Librarianu se nepodařilo připravit. Ostatní části kurzu zůstávají dostupné.')
        return False
    return True


@st.cache_resource(show_spinner=False)
def ensure_models():
    cache=Path(os.environ.get('ML_LIBRARIAN_CACHE',str(ROOT/'.cache/hf')))
    pinned=[('intfloat/multilingual-e5-small','614241f622f53c4eeff9890bdc4f31cfecc418b3'),
            ('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1','1427fd652930e4ba29e8149678df786c240d8825')]
    if not all((cache/('models--'+name.replace('/','--'))/'snapshots'/revision/'model.safetensors').is_file() for name,revision in pinned):
        with st.spinner('Připravuji připnuté modely pro vyhledávání…'):
            from prepare_runtime_models import prepare
            prepare()
    return True


@st.cache_resource(show_spinner=False)
def get_search_index():
    sys.path.insert(0,str(ROOT/'src/librarian'))
    from search import E5SearchIndex
    return E5SearchIndex.load()
