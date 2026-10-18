"""Read-only development evidence and executable notebook downloads."""
import json
from pathlib import Path
import streamlit as st
ROOT=Path(__file__).resolve().parents[2]


def render_lecturer():
    st.title('ML Projekt Librarian')
    st.caption('Od vlastních zápisků z kurzu k vyhledávání a odpovědím s dohledatelnými zdroji.')
    st.markdown('**Záměr → volba nástrojů → dvoudenní plán → experimenty a slepé uličky → poučení**')
    for number in range(1,6):
        st.markdown((ROOT/f'docs/lecturer/story_{number:02d}.md').read_text(encoding='utf-8'))
        if number==4:
            with st.expander('Použité metody · navázat na výklad v kurzu'):
                methods=[('Příprava dat, škálování a pipelines','views/00_prework_workflow.py'),
                    ('Bag of Words a TF-IDF','views/04_nlp_bow_tfidf_theory.py'),
                    ('Transformery a Hugging Face','views/04_nlp_bert_theory.py'),
                    ('Hyperparametry a křížová validace','views/03_hyperparameter_tuning_theory.py'),
                    ('RAG a agenti','views/06_modern_ml_rag_agents.py'),
                    ('Produkční nasazení a MLOps','views/06_mlops_productionizing.py')]
                if ROOT.parent.name=='components':
                    from course_links import source_pages
                    links=source_pages(str(ROOT.parent.parent))
                    for title,page in methods:
                        if page in links:st.page_link(page,label=title)
                else:
                    for title,page in methods:st.caption(title+' · '+page)
            with st.expander('Google Colab · čtyři reprodukovatelné kroky projektu'):
                st.caption('Od přípravy dat přes vyhledávání a evaluaci po experimenty s učením. Notebooky potřebují projektová data a závislosti; lokální běh není potvrzení běhu v Colabu.')
                for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
                    nb=json.loads(path.read_text(encoding='utf-8'))
                    st.write(''.join(nb['cells'][0]['source']).splitlines()[0].lstrip('# '))
                    st.download_button('Stáhnout '+path.name,path.read_bytes(),file_name=path.name,mime='application/x-ipynb+json',key='nb_'+path.stem)
                    st.link_button('Otevřít v Google Colab','https://colab.research.google.com/github/Kilitar/ML_Librarian/blob/master/notebooks/'+path.name)
        if number<5:st.divider()

    st.divider()
    st.subheader('Podklady k příběhu')
    with st.expander('Metodické detaily jednotlivých etap'):
        catalog=json.loads((ROOT/'docs/lecturer/catalog.json').read_text(encoding='utf-8'))
        selected=st.selectbox('Oblast vývoje',range(len(catalog)),format_func=lambda i:catalog[i]['title'],key='lecturer_section')
        st.markdown((ROOT/catalog[selected]['path']).read_text(encoding='utf-8'))
    with st.expander('Skutečné uložené souhrny experimentů'):
        names=['supervised_pair_summary.json','supervised_pair_v2_summary.json','base_calibration_diagnostic_summary.json','source_group_extension_summary.json']
        name=st.selectbox('Experiment',names,key='lecturer_summary');path=ROOT/'eval'/name
        if path.exists():
            st.json(json.loads(path.read_text(encoding='utf-8')))
            st.download_button('Stáhnout souhrn',path.read_bytes(),file_name=path.name,mime='application/json')
    with st.expander('Použitý projektový kód'):
        choices=['ingest.py','chunk.py','build_curated_corpus.py','search.py','rerank.py','calibration_data.py','train_supervised_pairs.py','train_supervised_pair_v2.py','answer_generation.py']
        name=st.selectbox('Modul',choices,key='lecturer_code');path=ROOT/'src/librarian'/name
        if path.exists():
            st.code(path.read_text(encoding='utf-8'),language='python')
            st.download_button('Stáhnout modul',path.read_bytes(),file_name=path.name)

    with st.expander('Úplný archiv vývojové dokumentace a experimentů'):
        st.caption('Dobové dokumenty mohou popisovat starší rozhodnutí. Aktuální stav určují roadmapa, DEMO_GENERATION a STREAMLIT_DEPLOYMENT; historická metrika není aktuální přejímka.')
        paths=sorted((ROOT/'docs').glob('*.md'))
        chosen=st.selectbox('Vývojový dokument',range(len(paths)),format_func=lambda i:paths[i].stem,key='lecturer_archive')
        path=paths[chosen]
        st.markdown(path.read_text(encoding='utf-8'))
        st.download_button('Stáhnout dokument',path.read_bytes(),file_name=path.name,mime='text/markdown')
