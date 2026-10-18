## 2 · Nejdřív rozhodnutí, potom nástroje

Začali jsme rozborem dat a návrhem cesty od dokumentu k odpovědi. Každý formát potřeboval jiný způsob čtení: PDF po stranách, Markdown po oddílech, notebooky podle textových buněk a Streamlit podle statických textových literálů. Kurzové skripty ani notebooky jsme při ingestu nespouštěli.

| Potřeba | Zvolený přístup | Důvod a kompromis |
|---|---|---|
| Dohledat původ tvrzení | Snapshot, cesta, locator a ID pasáže | Výsledek musí být možné zpětně zkontrolovat. |
| Hledat přesné termíny i význam | TF-IDF a vícejazyčné embeddingy E5 | Lexikální shoda doplňuje významovou podobnost; ani jedna sama nezaručuje odpověď. |
| Seřadit kandidáty | Cross-encoder | Posoudí otázku společně s pasáží; na CPU přidává latenci. |
| Rozpoznat slabé podklady | Evidence gate | Slabou shodu nechceme vydávat za dostatečnou oporu. Hranice má známá selhání. |
| Zformulovat odpověď | Model přes Groq, citace kontrolované aplikací | Snadná ukázka celého RAGu, ale závislost na síti a kvótě. |
| Rozšířit existující kurz | Modul a pravý dock ve Streamlitu | Pomocník je dostupný při studiu, bez přechodu do jiné aplikace. |

**Data analyst** zde řešil inventuru, kvalitu a duplicity. **Data scientist** reprezentaci textu, experimenty, anotaci a evaluaci. **Engineering** jejich propojení, testy, stav relace a veřejné nasazení. V malém projektu se tyto role přirozeně prolínají.
