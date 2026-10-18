## 1 · Ze zápisků z kurzu k vlastnímu RAGu

Můj Streamlit původně sloužil jako osobní **záznamník a zápisky z kurzu Coders Lab**. Vedle teorie v něm postupně přibývaly příklady, rozbory a notebooky. Nástroj jsem sdílel s lektorem i kolegy v kurzu. Byl opakovaně využíván nejen mnou, což mě potěšilo.

Pro samostatný projekt v závěru kurzu jsem chtěl využít to, co jsem se naučil, a prakticky to aplikovat na existující prostředí místo původního kurzového příkladu. Zároveň jsem se chtěl samostatně naučit něco nad rámec obsahu kurzu.

Rozhodl jsem se proto tuto existující aplikaci rozšířit o pomocníka: položit otázku vlastními slovy, najít oporu v materiálech a dostat vysvětlení s dohledatelnými zdroji. Tak vznikl záměr projektu **ML Librarian**.

**Co jsme chtěli ověřit:** zda dokážeme sestavit RAG nad nestrukturovanou dokumentací z PDF, Markdownů, textů Streamlitu, příkladů a Jupyter notebooků. RAG nejprve vyhledá podklady a teprve potom je předá jazykovému modelu pro sestavení odpovědi.

Nešlo o trénování vlastního velkého jazykového modelu. Výzvou bylo připravit různorodá data, vybrat správné pasáže a vrátit uživatele ke zdroji. Výsledkem měla být prezentace, kterou lektor otevře přes veřejný odkaz bez instalace a bez vlastního API klíče.

### Jak projekt vznikal

Projekt byl zpracován **AI orchestrací ve spolupráci s GPT 6**. Průběžnou oponenturu zajišťovaly **Gemini Argon a Claude 5**. Tento popis spolupráce vychází ze zkušenosti autora projektu.

Jednotlivé kroky implementačního plánu jsem jako uživatel průběžně konzultoval a ověřoval. Zadával jsem směr, zkoušel výsledky v aplikaci, vracel konkrétní připomínky a rozhodoval o prioritách i změnách postupu. AI spolupráce tak byla součástí procesu učení, experimentování a implementace.

Oponentura modelů a moje průběžná kontrola popisují způsob práce. Nejsou náhradou nezávislé přejímky kvality vyhledávání a odpovědí, jejíž stav rozlišujeme v závěru.
