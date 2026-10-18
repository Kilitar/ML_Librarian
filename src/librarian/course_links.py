"""Resolve corpus sources to registered course pages without executing course code."""
import ast
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=4)
def source_pages(course_root):
    root=Path(course_root)
    tree=ast.parse((root/'app.py').read_text(encoding='utf-8-sig'))
    declared={}
    active=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and ast.unparse(node.func)=='st.navigation':
            active.update(n.id for n in ast.walk(node) if isinstance(n,ast.Name))
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and ast.unparse(node.value.func)=='st.Page':
            call=node.value
            if call.args and isinstance(call.args[0],ast.Constant) and isinstance(call.args[0].value,str):
                for target in node.targets:
                    if isinstance(target,ast.Name):declared[target.id]=call.args[0].value
    registered=sorted({path for name,path in declared.items() if name in active})
    mapping={page:page for page in registered}
    for page in registered:
        path=root/page
        if not path.is_file():continue
        view=ast.parse(path.read_text(encoding='utf-8-sig'))
        names={}
        def resolve(node):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):return node.value
            if isinstance(node,ast.Name):return names.get(node.id)
            if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):
                left,right=resolve(node.left),resolve(node.right)
                if left is not None and right is not None:return '/'.join(x for x in (left,right) if x)
            if isinstance(node,ast.Call) and ast.unparse(node.func)=='Path' and node.args:return resolve(node.args[0])
            if ast.unparse(node)=='Path(__file__).resolve().parent.parent':return ''
            return None
        for node in ast.walk(view):
            if isinstance(node,ast.Assign):
                value=resolve(node.value)
                if value is not None:
                    for target in node.targets:
                        if isinstance(target,ast.Name):names[target.id]=value
        candidates=list(names.values())+[n.value for n in ast.walk(view) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        for candidate in candidates:
            relative=Path(candidate)
            if relative.suffix.lower() not in ('.md','.ipynb','.pdf','.txt') or relative.is_absolute() or '..' in relative.parts:continue
            if (root/relative).is_file():mapping.setdefault(relative.as_posix(),page)
    return mapping


# Reviewed editorial associations, not claims that page text equals source text.
RELATED_PAGES = {
    '06_Final_Project/theory/04_modern_ml_2026_rag_agents_lora.md':
        'views/06_modern_ml_rag_agents.py',
}
PDF_NOTICE = ('Zdrojová PDF nejsou součástí veřejné webové aplikace; obsahuje pouze jejich '
              'zpracované textové úryvky (chunks). Materiály jsou autorským majetkem Coders Lab '
              'a jsou určeny studentům a absolventům kurzu, nejsou veřejně dostupné. '
              'Proto zde není odkaz na originální PDF.')


def course_link_info(source, course_root):
    path=str(source.get('source_path','')).replace('\\','/')
    lower=path.lower()
    pdf=(source.get('source_origin')=='Coderslab PDF' or lower.endswith('.pdf') or
         (lower.startswith('resources/') and ('pdf' in lower or source.get('source_kind')=='pdf')))
    if pdf:return {'page':None,'label':None,'notice':PDF_NOTICE}
    mapping=source_pages(str(course_root))
    page=mapping.get(path)
    if page:return {'page':page,'label':'Otevřít v kurzu','notice':None}
    related=RELATED_PAGES.get(path)
    if related and mapping.get(related)==related:
        return {'page':related,'label':'Související stránka kurzu',
                'notice':'Stránka vysvětluje stejné téma; její obsah se může lišit od nalezeného úryvku.'}
    return {'page':None,'label':None,
            'notice':'Materiál nemá samostatnou stránku v kurzu; nalezený úryvek je níže.'}


def render_course_link(source):
    # Only embedded in the host that owns st.navigation; standalone keeps its viewer.
    module_root=Path(__file__).resolve().parents[2]
    if module_root.parent.name!='components':return
    import streamlit as st
    info=course_link_info(source,module_root.parent.parent)
    if info['page']:st.page_link(info['page'],label=info['label'],icon='↗️')
    if info['notice']:st.caption(info['notice'])
