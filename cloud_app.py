"""Cloud entrypoint: operator artifact provisioning, lecturer docs available without corpus."""
import runpy
import sys
from pathlib import Path
import streamlit as st
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src/librarian'))
from deployment_bundle import fetch


@st.cache_resource(show_spinner=False)
def provision(url,checksum):
    fetch(url,checksum)
    from prepare_runtime_models import prepare
    prepare()
    return True


try:
    configured=bool(st.secrets.get('RUNTIME_BUNDLE_URL')) and bool(st.secrets.get('RUNTIME_BUNDLE_SHA256'))
except FileNotFoundError:
    configured=False
if configured:
    try:
        with st.spinner('Připravuji korpus a modely pro prezentaci…'):
            provision(st.secrets['RUNTIME_BUNDLE_URL'],st.secrets['RUNTIME_BUNDLE_SHA256'])
    except Exception:
        st.error('Příprava dat nebo modelů selhala. Provozovatel musí zkontrolovat balíček, SHA a dostupnost modelů.')
        from lecturer_view import render_lecturer
        render_lecturer();st.stop()
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
else:
    st.title('ML Librarian · příprava nasazení')
    st.info('Provozovatel ještě nenastavil ověřený datový balíček. Dokumentace pro lektora je dostupná níže; vyhledávání zatím není aktivní.')
    from lecturer_view import render_lecturer
    render_lecturer()
