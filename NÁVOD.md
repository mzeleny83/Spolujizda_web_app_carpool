# 🚗 Spolujízda - Návod k použití

## 📋 Jak spustit aplikaci

### 1. Spuštění backend serveru
```bash
cd /home/win/Desktop/Programování/AI-Editor/Projekt
pip install -r requirements.txt
python app.py
```
Server poběží na: http://localhost:5000

### 2. Spuštění Flutter aplikace

#### 🌐 Webová verze (nejjednodušší)
```bash
flutter pub get
flutter run -d chrome
```

#### 📱 Android verze
```bash
flutter run -d android
```

#### 🍎 iOS verze
```bash
flutter run -d ios
```

## 🎯 Jak používat aplikaci

### 1. **Registrace a přihlášení**
- Otevřete aplikaci
- Klikněte "Registrovat se"
- Vyplňte jméno, email, telefon, heslo
- Přihlaste se pomocí emailu a hesla

### 2. **Hlavní menu (5 možností)**
- 🚗 **Nabídnout jízdu** - Pokud jedete autem
- 🔍 **Hledat jízdu** - Pokud potřebujete svézt
- 👥 **Moje shody** - Nalezené spolujízdy
- 💬 **Zprávy** - Chat s ostatními
- 🗺️ **Mapa řidičů** - **NOVÁ FUNKCE!**

### 3. **🗺️ Mapa řidičů - Hlavní funkce**

#### Jak funguje mapa:
1. **Klikněte na "Mapa řidičů"**
2. **Povolte lokalizaci** když se aplikace zeptá
3. **Uvidíte:**
   - 🔵 **Modrý marker** = Vaše poloha
   - 🟢 **Zelené markery** = Dostupní řidiči v okolí

#### Jak kontaktovat řidiče:
1. **Klikněte na zelený marker** řidiče
2. **Zobrazí se info okno** s detaily:
   - Jméno řidiče
   - Trasa (odkud → kam)
   - Čas odjezdu
   - Počet volných míst
   - Cena za osobu
3. **Máte 2 možnosti:**
   - 💬 **"Kontaktovat"** - Otevře chat
   - 🎫 **"Rezervovat"** - Pošle žádost o jízdu

#### Navigace na mapě:
- 📍 **Tlačítko "Moje poloha"** - Vrátí mapu na vaši pozici
- 🔍 **Plovoucí tlačítko** - Rychlé hledání jízd
- 👆 **Dotykem** na marker zobrazíte detaily

### 4. **Nabídka jízdy**
- Vyplňte: Odkud → Kam
- Nastavte čas odjezdu
- Zadejte počet volných míst
- Určete cenu za osobu

### 5. **Hledání jízdy**
- Zadejte trasu: Odkud → Kam  
- Vyberte čas odjezdu
- Aplikace najde dostupné jízdy

### 6. **Chat a komunikace**
- V seznamu shod klikněte "Kontakt"
- Pište zprávy s řidičem/spolucestujícím
- Domluvte si detaily (místo setkání, atd.)

## 🔧 Řešení problémů

### Mapa se nezobrazuje:
1. Zkontrolujte internetové připojení
2. Povolte lokalizaci v nastavení telefonu
3. Restartujte aplikaciju

### Backend server nefunguje:
```bash
# Zkontrolujte, zda běží na portu 5000
netstat -an | grep 5000

# Restartujte server
python app.py
```

### Flutter aplikace se nespustí:
```bash
# Vyčistěte cache
flutter clean
flutter pub get

# Spusťte znovu
flutter run -d chrome
```

## 💡 Tipy pro použití

1. **Nejdříve spusťte backend server** (python app.py)
2. **Pak spusťte Flutter aplikaci** (flutter run -d chrome)
3. **Povolte lokalizaci** pro nejlepší zážitek
4. **Používejte mapu** pro rychlé nalezení řidičů v okolí
5. **Komunikujte přes chat** před jízdou

## 🎯 Hlavní výhody mapy

- **Vidíte řidiče v reálném čase** na mapě
- **Rychlé kontaktování** jedním kliknutím
- **Přehledné informace** o každé jízdě
- **Automatická lokalizace** vaší polohy
- **Intuitivní ovládání** dotykem

Aplikace je nyní připravena k použití! 🚀