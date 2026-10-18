## 5 · Co si odnášíme a kam pokračovat

Největší část experimentálního úsilí podle průběhu vývoje spotřebovalo ladění vyhledávání, abstence a evaluace. Přesný podíl hodin nemáme změřený. Další náročnou částí bylo převést lokálně fungující řešení do veřejné aplikace: data, modely, konfigurace, kvóty a navigace.

**Co jsme ověřili:** různorodé studijní materiály lze převést do dohledatelných pasáží, prohledávat je a propojit s původními stránkami kurzu. Lokálně prošlo i generování s platnými citacemi. Ve veřejném nasazení fungovalo vyhledávání; poslední ověření generování skončilo limitem HTTP 429 po předchozích chybách citací a HTTP 400. Celé veřejné demo proto zatím nemá potvrzený úspěšný průchod. Tento stav popisuje poslední zaznamenané ověření, nikoli živý monitoring.

**Co zatím netvrdíme:** že relevance znamená pravdivost, že doslovná citace zaručuje správný výklad nebo že je kvalita nezávisle přijata. Původní přejímka zůstala nesplněná a další evaluaci jsme odložili.

### Kde má ověřený přístup praktický smysl

- **Firemní znalostní báze:** hledání souvislostí napříč nestandardizovanými PDF, návody, zápisy a interními texty.
- **Podpora servisního oddělení:** dohledání servisního postupu a jeho konkrétní verze ve firemní dokumentaci.
- **Onboarding:** vysvětlení interních procesů s odkazem na odpovědnou směrnici nebo návod.
- **Studijní a projektový deník:** propojení vlastních poznámek, příkladů a experimentů tak, aby se k nim člověk dokázal vracet pomocí otázek.

Přenos do firmy by vyžadoval další práci: oprávnění ke zdrojům, aktualizace a verzování dokumentů, ochranu dat a ověření kvality s lidmi z dané oblasti. Není to automaticky hotový produkt pro citlivé prostředí.

**Další smysluplný krok:** spolehlivě ověřit veřejný průchod s citacemi, ošetřit limity služby a projít reprezentativní odpovědi s lektorem. Potom rozvíjet to, co zlepší užitek pro člověka; další fine-tuning má smysl až s vhodnými daty a měřitelným přínosem.

### Poděkování

Děkuji **Coders Lab za kurz**, který poskytl znalostní základ i inspiraci pro tento projekt, a **Monice za vedení kurzu a předávání zkušeností**. Z vlastních kurzových zápisků vznikl prostor pro praktické experimentování a pro učení nejen z toho, co fungovalo, ale i z chyb a slepých uliček.
