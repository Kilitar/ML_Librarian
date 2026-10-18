# Od studijních materiálů k odpovědi s dohledatelnou oporou

Cíl: lektor otevře připravenou Streamlit prezentaci, položí CZ/EN/PL otázku a prohlédne odpověď i její zdroje. Netrénujeme vlastní velký jazykový model. Hlavní práce je příprava dat, vyhledávání, měření a rozhodování, kdy neodpovídat.

**Tok dat:** neměnný snapshot → statická extrakce → chunkování → deduplikace → E5/TF-IDF kandidáti → cross-encoder → výběr pasáží a evidence gate → volitelné generování s kontrolou citací.

Zdrojový kurz je read-only. Notebooky ani Python stránky kurzu při ingestu nespouštíme. Zpracováváme Markdown, PDF po stranách, notebookový Markdown a statické literály Streamlit stránek; zachováváme cestu, locator, jazyk a chunk ID.

Aktuální index:4189pasáží ×384rozměrů. Počet zdrojů a skutečné rozdělení ověřuje notebook přímo z korpusu. Starší zprávy se4196pasážemi popisují dřívější index.

**Data analyst:** inventura, datová kvalita, duplicity a explorace. **Data scientist:** reprezentace, návrh experimentů, anotace a evaluace. **Engineering:** fingerprinty, izolace, UI, testy a nasazení. Role se překrývají.

Lokální funkčnost, automatické testy, živá kvalita odpovědi a veřejné nasazení jsou odlišné stavy. Přejímka kvality zůstává nesplněná.
