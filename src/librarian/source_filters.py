"""Filter vocabulary matches the existing path-derived source tags."""
SOURCE_ROLES = ('Cvičení / úkol','Teorie / analýza','Shrnutí / přehled','Příklad / implementace','Studijní materiál')
SOURCE_ORIGINS = ('Coderslab PDF','Kurzové poznámky','Streamlit prezentace','Notebook')


def exclusions(values, options):
    if values is None:
        return set()
    if isinstance(values,str):
        raise ValueError('Source filters must be a collection of tag names')
    selected = set(values)
    if selected - set(options):
        raise ValueError('Unknown source filter')
    return selected


def allowed_indices(documents, classify, hidden_roles, hidden_origins):
    allowed=[]
    for i,document in enumerate(documents):
        tags=classify(document)
        if tags['source_role'] not in hidden_roles and tags['source_origin'] not in hidden_origins:
            allowed.append(i)
    return allowed


def selected_exclusions(roles, origins):
    selected_roles=exclusions(roles,SOURCE_ROLES)
    selected_origins=exclusions(origins,SOURCE_ORIGINS)
    if not selected_roles or not selected_origins:
        raise ValueError('Vyber alespoň jeden typ materiálu a jeden původ zdroje.')
    return ([role for role in SOURCE_ROLES if role not in selected_roles],
            [origin for origin in SOURCE_ORIGINS if origin not in selected_origins])


def render_source_selection(prefix, *, hidden_roles=(), hidden_origins=()):
    import streamlit as st
    st.caption('Hledat v zaškrtnutých skupinách. Výběr se použije po kliknutí na Vyhledat zdroje.')
    st.markdown('**Typ materiálu**')
    roles=[role for i,role in enumerate(SOURCE_ROLES)
           if st.checkbox(role,value=role not in hidden_roles,key=f'{prefix}_role_{i}')]
    st.markdown('**Původ zdroje**')
    origins=[origin for i,origin in enumerate(SOURCE_ORIGINS)
             if st.checkbox(origin,value=origin not in hidden_origins,key=f'{prefix}_origin_{i}')]
    return roles,origins
