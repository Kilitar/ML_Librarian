## 3 · Dva dny jako rozpočtový rámec

Cílem bylo udržet projekt ve dvoudenním pracovním rozsahu. Původní roadmapa a implementační plán jsou dostupné v rozbalitelných podkladech pod touto kapitolou. Následující časová osa je **zpětné rozdělení práce do dvou osmihodinových dnů** pro přehlednou prezentaci, nikoli doslovná kopie původního plánu. Přesný výkaz odpracovaných hodin nemáme.

| Časový blok | Hlavní výstup | Hranice rozsahu |
|---|---|---|
| Den 1 · 0–2 h | Inventura dat, návrh a ověřovací dotazy | Vybrat reprezentativní obsah, nesnažit se rozumět všem formátům dokonale. |
| Den 1 · 2–5 h | Extrakce, chunkování, původ a deduplikace | Vytvořit reprodukovatelný korpus. |
| Den 1 · 5–8 h | Funkční vyhledávání a viditelné zdroje | Porovnat základní přístupy a stanovit konec ladění. |
| Den 2 · 0–3 h | Odpověď s citacemi a chybové stavy | Dotáhnout celou cestu otázka → podklady → odpověď. |
| Den 2 · 3–6 h | Integrace do kurzu a veřejné nasazení | Ověřit cloud, konfiguraci a odkazy. |
| Den 2 · 6–8 h | Kontrola, příběh projektu a rezerva | Připravit demonstraci a otevřeně popsat limity. |

**Klíčové funkce:** vyhledání pasáží, dohledatelné zdroje, odpověď s citacemi, použití v existujícím Streamlitu a veřejná prezentace.

**Bonusy až po dokončení základu:** širší vícejazyčné ladění, filtry, vlastní doménový klasifikátor, fine-tuning a rozsáhlejší evaluační experimenty.

### Kde se plán rozešel se skutečností

Vyhledávání a evaluace se rozrostly do mnoha iterací ještě před dokončením celého dema. Rozšířili jsme práci o slovníkové opravy, doménové kontroly, vlastní učení a audit kalibrace. **Tuto část jsme proti záměru výrazně přetáhli.**

Rozhodnutí bylo další ladění odložit a přesunout pozornost k integraci, generování a nasazení. Nebyla to splněná přejímka kvality; byla to vědomá změna priority. Příště má každá experimentální větev dostat časový limit a jasné rozhodnutí: použít, odložit, nebo ukončit.
