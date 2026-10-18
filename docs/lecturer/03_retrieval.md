# Výběr podkladů

TF-IDF je lexikální baseline. E5 používá prefixy query:/passage: a normalizované vektory; skalární součin odpovídá kosinové podobnosti. Kandidáti z obou metod se sjednotí, cross-encoder posoudí dotaz a pasáž společně.

Semantic layer obsahuje explicitní doménové vazby a synonyma, např. zkratku a rozvinutí pojmu. Je to řízená znalostní/heuristická vrstva, nikoli nově naučená neuronová znalost. Vyžaduje ablace a regresní kontrolu.

Diverzifikace omezuje duplicity. Filtry původu/role se použijí před retrievalem; doplňkový kontext nesmí vrátit skrytý zdroj. Skutečné nadpisy mohou vysvětlit fragment. Relevance je pořadové skóre, nikoli pravděpodobnost správnosti odpovědi. MRR je agregovaná metrika, nikoli hodnota jedné karty.

Notebook02 používá skutečný E5SearchIndex v režimech e5/hybrid/rerank. Náročné kroky jsou explicitní; nevytváří náhradní syntetická tvrzení o výkonu. Produkční revize jsou připnuté v domain_guard.py a rerank.py.
