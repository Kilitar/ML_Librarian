## 4 · Vývoj: co nás naučila cesta

### Od souborů k dohledatelným pasážím

**Problém:** formáty i struktura textů se lišily a stejné informace se opakovaly. **Pokus:** statická extrakce, chunkování a deduplikace se zachováním původu. **Výsledek:** index 4 189 pasáží s embeddingy o 384 rozměrech. **Rozhodnutí:** oddělit přípravu dat od webového běhu a ponechat možnost dohledat originál.

### Správné téma ještě není správná odpověď

**Problém:** „kolik je hodin“ vracelo slabé výsledky; „Který řízek je nejlepší pro decision tree?“ obsahovalo známý termín a dokázalo zmást hodnocení relevance. **Pokus:** kombinace TF-IDF, E5, rerankingu a evidence gate. **Poučení:** podobnost, doménová příslušnost a odpověditelnost jsou různé věci. Skóre relevance není pravděpodobnost správnosti.

### Slovníková spirála

**Problém:** „hluboké učení“ a „deep learning“ nebo otázka na zkratku ML nedávaly stejně užitečné výsledky. **Pokus:** omezené mapování pojmů a zkratek. **Výsledek:** pomohlo známým formulacím. **Rozhodnutí:** přiznat, že jde o pravidla, nikoli naučené obecné porozumění. Další synonymum samo o sobě není důkaz lepšího modelu.

### Fine-tuning, který jsme nenasadili

**Hypotéza:** malé dotrénování rerankeru zlepší rozlišení odpovědi od pouhé zmínky. **Pokus:** varianty supervised v1/v2. **Výsledek:** v1 na 45 nových párech nezlepšilo binární matici proti základu; v2 v kontrastním experimentu ztratilo část přímých odpovědí. **Rozhodnutí:** checkpointy nepoužít v produkci. Nepovýšit neúspěšný experiment je stejně důležité jako umět model natrénovat.

### Více dat neznamená nezávislý test

**Problém:** nové formulace sdílely zdroje nebo text se staršími daty. **Pokus:** seskupit páry tranzitivně podle dotazu, zdroje a obsahu. **Výsledek:** všech 120 dodatečně anotovaných výsledků se připojilo ke starším fitovaným datům. **Poučení:** bránit leakage a po prohlédnutí výsledků přestat příklady vydávat za neviděný test. Dosavadní anotace jsou pracovní hodnocení, ne nezávislá lidská přejímka.

### Poslední míle je součást produktu

Původní formulář s vlastním klíčem lektora neodpovídal cíli hotové prezentace. Přesunuli jsme konfiguraci na provozovatele, integrovali pravý dock a doplnili odkazy do kurzu. V cloudu nás zastavil ukázkový text místo API klíče, potom nepřesné citace modelu a limit free tieru. Doplnili jsme bezpečnou diagnostiku a jeden omezený opravný pokus; přesnou kontrolu citací jsme zachovali.

**Slepá ulička není slabina, pokud ji umíme rozpoznat, vyhodnotit a změnit postup.** Síla je ve schopnosti dotáhnout celek, ne v množství experimentů. Funkčnost však musíme doložit: lokální test, veřejné vyhledávání a úspěšná veřejná odpověď jsou tři odlišné výsledky.
