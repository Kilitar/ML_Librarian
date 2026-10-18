# Inventura a datová kvalita

Vymezili jsme allowlist, vynechali .git/.venv/cache/secrets, vytvořili SHA-256 manifest snapshotu, staticky extrahovali text a rozdělili jej na pasáže s proveniencí. Kontroly: počty podle typu souboru, prázdný obsah, délky pasáží a duplicity.

Příliš krátké pasáže ztrácely definici či nadpis. HTML obaly zhoršovaly čitelnost. Sousední kontext doplňujeme jen z ověřeného stejného zdroje. Rozpadlé ASCII diagramy a viditelný Markdown byly prezentační chyby; oprava vykreslení sama nezlepšuje relevanci ani správnost zdroje.

Kód: ingest.py, chunk.py, build_curated_corpus.py, source_viewer.py, snippet_format.py. Notebook 01 provádí inventuru skutečného přeneseného korpusu bez spouštění kurzového kódu.
