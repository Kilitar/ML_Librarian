# Hypotéza → experiment → výsledek → rozhodnutí

| Iterace | Hypotéza a zásah | Pozorování | Rozhodnutí |
|---|---|---|---|
| E5/TF-IDF/cross-encoder | Kombinace kandidátů a párové skórování | Rozumné zdroje, ale téma zaměňováno za odpověď | Funkční základ, ne důkaz pravdivosti |
| Doménový guard v1 | Naučená hranice pomůže šedé zóně | Oprava známého dotazu na polévku, bez doloženého nového přínosu | Úzká oprava |
| Širší doménové učení | Více negativních domén pomůže silným nesouvisejícím dotazům | Známé palačinky zůstaly problém | Experiment nepovýšen na obecné řešení |
| Qwen answerability | Jiný model posoudí celé pokrytí | Opravil známý nesmysl, další selhávaly | Nepromováno |
| Supervised v1 | Poslední blok + hlava, 40 binárních trénovacích párů | Na 45 nových párech stejná binární matice base/v1 | Přínos neprokázán |
| Supervised v2 | Přidat 8 negativů se špatným vztahem | 18 source-informed párů: přímé odpovědi 5/6 → 4/6 → 4/6 base/v1/v2; pořadí kontrastů 6/6 u všech | Checkpoint nepoužit |
| Kalibrační audit | Lepší anotace a fit/calibration/test rozdělení | Tranzitivní leakage; více dat nestačí jako nezávislost | Data zachovat, další ladění odložit |
| Celý RAG | Ověřit užitečnost odpovědi s citacemi | Formát/UI otestovány; živá Groq kvalita neověřena | Prototyp se známými limity |

V1/v2 neuronové checkpointy nejsou produkční. Notebook 04 defaultně čte skutečné výsledky; trénování vyžaduje explicitní přepínač, development data a stažení vah. GPU běh přímo v Colab není dosud ověřený.
