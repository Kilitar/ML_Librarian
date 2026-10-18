## 1 · Ze zápisků z kurzu k vlastnímu RAGu

Můj Streamlit původně sloužil jako osobní **záznamník a zápisky z kurzu Coders Lab**. Vedle teorie v něm postupně přibývaly příklady, rozbory a notebooky. Obsah byl užitečný, ale s jeho růstem bylo stále těžší rychle najít konkrétní vysvětlení.

Chtěl jsem tuto existující aplikaci rozšířit o pomocníka: položit otázku vlastními slovy, najít oporu v materiálech a dostat vysvětlení s dohledatelnými zdroji. Tak vznikl záměr projektu **ML Librarian**.

**Co jsme chtěli ověřit:** zda dokážeme sestavit RAG nad nestrukturovanou dokumentací z PDF, Markdownů, textů Streamlitu, příkladů a Jupyter notebooků. RAG nejprve vyhledá podklady a teprve potom je předá jazykovému modelu pro sestavení odpovědi.

Nešlo o trénování vlastního velkého jazykového modelu. Výzvou bylo připravit různorodá data, vybrat správné pasáže a vrátit uživatele ke zdroji. Výsledkem měla být prezentace, kterou lektor otevře přes veřejný odkaz bez instalace a bez vlastního API klíče.
