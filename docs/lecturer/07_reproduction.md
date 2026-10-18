# Reprodukce

Notebooky01–04 obsahují skutečný použitý kód nebo přímo volají jeho projektové moduly. Pro analýzu, retrieval a prohlédnutí výsledků nepotřebují API klíč. Původní kurz není v Git repozitáři; skutečná data dodá provozovatel jako runtime/development balíček.

Runtime: kurátorované pasáže, extrahované dokumenty a E5 index. Development: skutečné anotace a uložené experimentální výstupy. Bez klíčů/cache/checkpointů. Balíčky nejsou automaticky veřejné. Kontroluj SHA a záznam git commitu.

Notebooky neobsahují předstírané výstupy. Lokální provedení buněk neověřuje přihlášení, upload a GPU běh přímo v Colab. Trénování je defaultně vypnuté.

Nasazení: modul v existujícím Streamlit kurzu, jeho app.py a requirements.txt, ověřený runtime balíček, připnuté veřejné váhy a serverový GROQ_API_KEY. Samostatný cloud_app.py je jen vývojová alternativa. Lokální URL není veřejné nasazení. Community Cloud potřebuje autentizované vytvoření aplikace, konfiguraci secrets/dat a test paměti/latence/kvality.

Minimální balíček neobsahuje originální soubory ke stažení; extrahovaný text zůstává dostupný a chybějící originál je v UI označen. Náročné modely mohou překročit free hosting limity; cloudová paměť zatím nezměřena. Viz STREAMLIT_DEPLOYMENT.md.
