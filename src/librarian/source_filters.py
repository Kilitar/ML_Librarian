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
