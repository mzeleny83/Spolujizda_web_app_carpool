# Spolujízda - Guest Mode (Demo režim)

## Nové funkce pro nepřihlášené uživatele

Aplikace Spolujízda nyní podporuje **demo režim** pro nepřihlášené uživatele, který umožňuje prozkoumat aplikaci a její funkce před registrací.

### Co je nového

#### 1. Úvodní obrazovka pro nepřihlášené uživatele
- Aplikace nyní začína v demo režimu (`/guest-home`)
- Jasné označení demo režimu s informacemi o omezeních
- Přehled dostupných a zamčených funkcí

#### 2. Dostupné funkce pro nepřihlášené uživatele

**✅ Prohlédnout jízdy** (`/guest-rides`)
- Zobrazení všech dostupných jízd
- Informace o řidičích, trasách, cenách a volných místech
- Upozornění na nutnost přihlášení pro rezervaci a chat

**✅ Mapa jízd** (`/guest-map`)
- Demo verze mapy s vizualizací jízd
- Informace o omezeních interaktivních funkcí
- Možnost prohlédnout rozmístění jízd

#### 3. Zamčené funkce (vyžadují přihlášení)
- 🔒 Hledání jízd
- 🔒 Nabídka jízd
- 🔒 Rezervace jízd
- 🔒 Chat s řidiči
- 🔒 Správa vlastních jízd
- 🔒 Zprávy a notifikace

### Navigace v aplikaci

#### Vstupní body
1. **Aplikace se spustí v demo režimu** - uživatel může ihned prozkoumat funkce
2. **Přihlášení** - přístup ke všem funkcím
3. **Registrace** - vytvoření nového účtu

#### Přechody mezi režimy
- **Demo → Přihlášení**: Tlačítka "Přihlásit se" na všech guest obrazovkách
- **Demo → Registrace**: Tlačítko "Registrovat se" na úvodní obrazovce
- **Přihlášen → Demo**: Tlačítko "Odhlásit se" v hlavní aplikaci

### Uživatelské rozhraní

#### Vizuální indikátory
- **Oranžové upozornění** na všech guest obrazovkách
- **Ikony zámku** u nedostupných funkcí
- **Šedé tlačítka** pro zamčené akce
- **Informační dialogy** při pokusu o použití zamčených funkcí

#### Konzistentní zprávy
- Jasné vysvětlení, proč je funkce nedostupná
- Snadný přístup k přihlášení/registraci
- Motivace k vytvoření účtu

### Technické změny

#### Nové soubory
```
lib/screens/guest_home_screen.dart      # Úvodní obrazovka pro nepřihlášené
lib/screens/guest_rides_screen.dart     # Prohlížení jízd bez přihlášení
lib/screens/guest_map_screen.dart       # Demo mapa
lib/services/auth_service.dart          # Služba pro správu autentifikace
```

#### Upravené soubory
```
lib/main.dart                          # Změna výchozí route na /guest-home
lib/screens/login_screen.dart          # Přidáno tlačítko "Prozkoumat bez přihlášení"
lib/screens/register_screen.dart       # Přidáno tlačítko "Prozkoumat bez registrace"
lib/screens/home_screen.dart           # Odhlášení přesměruje na guest režim
```

### Výhody pro uživatele

1. **Snížená bariéra vstupu** - uživatelé mohou aplikaci vyzkoušet bez registrace
2. **Lepší pochopení hodnoty** - vidí konkrétní jízdy a funkce před registrací
3. **Informované rozhodnutí** - rozumí, co získají registrací
4. **Flexibilní přístup** - mohou se kdykoli přihlásit nebo pokračovat v demo režimu

### Výhody pro vývojáře

1. **Vyšší konverze** - více uživatelů si aplikaci vyzkouší
2. **Lepší onboarding** - postupné seznámení s funkcemi
3. **Snížené opuštění** - uživatelé nemusí hned registrovat
4. **Jasná hodnota** - demonstrace přínosů aplikace

### Budoucí rozšíření

Možné další funkce pro demo režim:
- Omezený počet zobrazení jízd denně
- Ukázka jedné demo konverzace
- Interaktivní tutoriál
- Personalizované doporučení po registraci
- Analytics sledování chování v demo režimu