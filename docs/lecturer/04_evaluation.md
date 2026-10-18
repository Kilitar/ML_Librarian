# Co měříme

Oddělujeme pořadí relevantního dokumentu, pokrytí konkrétní otázky skutečnou pasáží, abstenci a faktickou správnost tvrzení. Správná cesta souboru nestačí jako gold label odpověditelnosti.

Štítky: direct / partial / topic_only / irrelevant / unjudgeable. Partial automaticky neznamená negativní třídu. Dosavadní štítky jsou provizorní hodnocení Codexu, nikoli nezávislá lidská přejímka.

Sdílený normalizovaný dotaz NEBO cesta zdroje NEBO totožný normalizovaný text propojuje páry tranzitivně. Parafráze a různé soubory ze stejného PDF mohou stále sdílet význam; počet komponent není počet nezávislých témat.

Po anotaci 120 výsledků z 24 dotazů: 42 direct, 36 partial, 42 negative. Všech 120 se tranzitivně připojilo ke starším fitovaným datům. Dalších 9 oddělených zdrojů dalo 27 source-informed kontrastních párů, nikoli nové výsledky retrievalu. Celkem 276 známých párů; base: 86 direct / 125 negative. Přísný source-transfer pool v1/v2: 11 direct / 22 negative, pod minimy 30 / 59.

Původní base na dřívějších 100 známých binárních párech nedosáhl 80 % recall při 0 empirických FP; maximum bylo 60 %. Nejde o odhad produkční bezpečnosti. Kvůli známému PCA příkladu jsme práh neposunuli.

12 rezervovaných otázek zůstává nespouštěných. Přejímka not_accepted. Další kalibraci uživatel odložil. Notebook 03 znovu seskupí skutečné development páry a porovná uložené souhrny; nevytváří nový held-out výsledek.
