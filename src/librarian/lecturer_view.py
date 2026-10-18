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
        if number==3:
            with st.expander('Původní roadmapa a checklist · plán versus uložený průběh'):
                st.caption('Původní dokumenty pocházejí z prvního commitu 988ebca. Pozdější checklist je uložený checkpoint, nikoli živý stav nasazení; jeho dobové poznámky mohou být překonané.')
                original_tab,checkpoint_tab=st.tabs(['Původní roadmapa','Pozdější stav checklistu'])
                for tab,filename,key in [(original_tab,'original_roadmap.json','original'),(checkpoint_tab,'roadmap_checkpoint.json','checkpoint')]:
                    with tab:
                        path=ROOT/'docs/lecturer'/filename
                        roadmap=json.loads(path.read_text(encoding='utf-8'))
                        st.write('Plánovaný rozsah: '+str(roadmap['total_estimate_hours'])+' hodin')
                        if roadmap.get('updated_at'):st.caption('Checkpoint: '+roadmap['updated_at'])
                        labels={'done':'☑ Hotovo','in_progress':'◐ Probíhá','deferred':'↷ Odloženo','todo':'☐ Čeká'}
                        for task in roadmap['tasks']:
                            st.markdown('**'+labels.get(task['status'],task['status'])+' · '+task['title']+'**')
                            st.caption(task['phase']+' · odhad '+str(task['estimate_hours'])+' h')
                            if task.get('detail'):st.write(task['detail'])
                        st.download_button('Stáhnout roadmapu a checklist',path.read_bytes(),file_name=filename,mime='application/json',key='roadmap_download_'+key)
            with st.expander('Původní implementační plán · úplné zadání'):
                plan=ROOT/'docs/lecturer/original_implementation_plan.md'
                st.caption('Historický dokument z commitu 988ebca, v původním znění. Pozdější integrace a rozhodnutí jsou popsány v příběhu projektu.')
                st.markdown(plan.read_text(encoding='utf-8'))
                st.download_button('Stáhnout původní plán',plan.read_bytes(),file_name='original_implementation_plan.md',mime='text/markdown')
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
