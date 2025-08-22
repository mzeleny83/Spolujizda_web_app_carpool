# 🧪 Testovací plán - Spolujízda

## 📋 Checklist pro testování

### ✅ 1. REGISTRACE A PŘIHLÁŠENÍ
- [ ] Registrace nového uživatele (jméno, telefon, heslo)
- [ ] Registrace s emailem (volitelné)
- [ ] Chyba při duplicitním telefonu
- [ ] Chyba při neplatném telefonu
- [ ] Chyba při neshodných heslech
- [ ] Přihlášení telefonem
- [ ] Přihlášení emailem
- [ ] Chyba při špatném heslu
- [ ] Odhlášení

### ✅ 2. NABÍZENÍ JÍZD
- [ ] Nabídka jízdy (přihlášený uživatel)
- [ ] Chyba při nabízení bez přihlášení
- [ ] Všechna povinná pole vyplněna
- [ ] Datum a čas v budoucnosti
- [ ] Počet míst 1-4
- [ ] Rozumná cena

### ✅ 3. VYHLEDÁVÁNÍ JÍZD
- [ ] Vyhledání podle města "odkud"
- [ ] Vyhledání podle města "kam"
- [ ] Vyhledání "odkud" + "kam"
- [ ] Zobrazení všech jízd
- [ ] Prázdný výsledek pro neexistující město
- [ ] Zobrazení detailů jízdy

### ✅ 4. MAPA
- [ ] Načtení mapy České republiky
- [ ] Zobrazení všech jízd na mapě
- [ ] Zelené "START" markery
- [ ] Červené "CÍL" markery
- [ ] Modré trasy mezi městy
- [ ] Kliknutí na marker zobrazí info
- [ ] Zoom in/out funguje
- [ ] Přetahování mapy

### ✅ 5. UŽIVATELSKÉ ROZHRANÍ
- [ ] Navigace mezi sekcemi
- [ ] Responzivní design (mobil/desktop)
- [ ] Správné zobrazení zpráv (úspěch/chyba)
- [ ] Formuláře se vyčistí po odeslání
- [ ] Tlačítka reagují na kliknutí

### ✅ 6. DATABÁZE
- [ ] Uživatelé se ukládají správně
- [ ] Jízdy se ukládají správně
- [ ] Hesla jsou hashovaná
- [ ] Telefony v jednotném formátu (+420...)
- [ ] Časové značky fungují

## 🔧 Testovací scénáře

### Scénář 1: Nový uživatel
1. Otevři http://localhost:8081
2. Klikni "Registrovat"
3. Vyplň: Jan Testovací, +420123456789, heslo123
4. Registruj se
5. Přihlaš se stejnými údaji
6. Ověř, že vidíš "Přihlášen jako: Jan Testovací"

### Scénář 2: Nabídka jízdy
1. Přihlaš se
2. Klikni "Nabídnout"
3. Vyplň: Praha → Brno, zítra 10:00, 2 místa, 300 Kč
4. Nabídni jízdu
5. Jdi na "Hledat" → "Všechny jízdy"
6. Ověř, že tvoje jízda je v seznamu

### Scénář 3: Vyhledávání
1. Jdi na "Hledat"
2. Zadej "Praha" do "Odkud"
3. Klikni "Hledat"
4. Ověř, že vidíš jízdy z Prahy
5. Zkus "Brno" do "Kam"
6. Ověř filtrování

### Scénář 4: Mapa
1. Klikni "🗺️ Mapa"
2. Ověř, že se načte mapa ČR
3. Najdi zelené "START" a červené "CÍL" značky
4. Klikni na značku
5. Ověř, že se zobrazí info o jízdě
6. Zkus zoom a přetahování

## 🐛 Časté chyby k testování

### Chyby registrace:
- Prázdná pole
- Neplatný telefon (123, abc)
- Duplicitní telefon
- Různá hesla

### Chyby přihlášení:
- Neexistující telefon
- Špatné heslo
- Prázdná pole

### Chyby nabízení:
- Nepřihlášený uživatel
- Prázdná pole
- Datum v minulosti
- Nulová cena

## 📱 Testování na zařízeních

### Desktop:
- [ ] Chrome
- [ ] Firefox
- [ ] Edge

### Mobil:
- [ ] Chrome mobile
- [ ] Safari mobile
- [ ] Responzivní design

## 🔍 Kontrola výkonu

### Rychlost:
- [ ] Načtení stránky < 3s
- [ ] Vyhledávání < 1s
- [ ] Mapa se načte < 5s

### Stabilita:
- [ ] Žádné JavaScript chyby v konzoli
- [ ] Server nepadá při chybných požadavcích
- [ ] Databáze se nepoškodí

## 📊 Testovací data

Vytvoř tyto testovací účty:
1. **Řidič1**: Jan Novák, +420111111111
2. **Řidič2**: Marie Svobodová, +420222222222
3. **Cestující**: Petr Dvořák, +420333333333

Vytvoř tyto testovací jízdy:
1. Praha → Brno (zítra 8:00, 3 místa, 250 Kč)
2. Brno → Ostrava (pozítří 15:00, 2 místa, 200 Kč)
3. Plzeň → Praha (dnes 18:00, 1 místo, 150 Kč)

## ✅ Finální kontrola

Před nasazením zkontroluj:
- [ ] Všechny funkce fungují
- [ ] Žádné chyby v konzoli
- [ ] Responzivní design
- [ ] Bezpečnost (hesla hashovaná)
- [ ] Výkon je dobrý
- [ ] Databáze je stabilní