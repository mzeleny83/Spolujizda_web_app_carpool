# 🚗 Spolujízda - Návod na spuštění a použití

## 🚀 Jak spustit aplikaci

### 1. Instalace závislostí
```bash
cd /home/win/Desktop/Programování/AI-Editor/Projekt
pip install -r requirements.txt
sudo snap install ngrok  # Pro veřejný přístup
```

### 2. Spuštění s veřejným odkazem (DOPORUČENO)
```bash
./start.sh
```
**NEBO**
```bash
python3 start_public.py
```

**Výstup bude:**
```
============================================================
🚀 SPOLUJÍZDA SERVER SPUŠTĚN!
============================================================
📱 Lokální přístup: http://127.0.0.1:5000
🌍 Veřejný odkaz:   https://abc123.ngrok.io
============================================================
📤 Pošlete tento odkaz kamarádovi:
   https://abc123.ngrok.io
============================================================
```

### 3. Spuštění pouze lokálně
```bash
python app.py
```

## 📱 Jak používat aplikaci

### 1. Základní nastavení
1. Otevřete aplikaci v prohlížeči
2. **Zadejte své jméno** do pole "Vaše jméno"
3. Klikněte na **"Začít sledování"** pro aktivaci GPS

### 2. Nabídka jízdy (pro řidiče)
1. Klikněte na **"Nabídnout jízdu"**
2. Vyplňte:
   - **Odkud**: Výchozí místo (např. "Praha, Wenceslas Square")
   - **Kam**: Cílové místo (např. "Brno, Hlavní nádraží")
   - **Datum a čas odjezdu**
   - **Počet volných míst** (1-8)
   - **Cena za osobu** v Kč
3. Klikněte **"Nabídnout"**

### 3. Hledání jízdy (pro spolucestující)
1. Klikněte na **"Hledat jízdu"**
2. Zadejte:
   - **Odkud**: Místo nástupu
   - **Kam**: Místo výstupu
3. Klikněte **"Hledat"**
4. Zobrazí se seznam dostupných jízd
5. Klikněte **"Kontaktovat řidiče"** u vybrané jízdy

### 4. Real-time sledování na mapě

#### Pro řidiče:
- Zapněte **"Začít sledování"** - vaše pozice se bude zobrazovat ostatním
- Vaše pozice je označena **modrou tečkou** 📍

#### Pro spolucestující:
- Zapněte **"Začít sledování"** pro svou pozicu
- Klikněte **"Aktivní jízdy"** pro zobrazení dostupných jízd
- Klikněte **"Sledovat na mapě"** u konkrétní jízdy
- Řidiči jsou označeni **červenou tečkou s autem** 🚗

### 5. Ovládání mapy
- **"Najít mě"**: Vycentruje mapu na vaši pozici
- **"Zobrazit všechny"**: Zobrazí všechny aktivní uživatele na mapě
- **Zoom**: Kolečko myši nebo gesta na mobilu

## 🔧 Řešení problémů

### GPS nefunguje
- **Povolte lokalizaci** v prohlížeči (objeví se výzva)
- **HTTPS**: Některé prohlížeče vyžadují HTTPS pro GPS
- **Mobilní zařízení**: Zkontrolujte nastavení lokalizace

### Mapa se nezobrazuje
- Aplikace funguje i **bez Google Maps API**
- Pozice se zobrazují **textově** pod mapou
- Pro plnou mapu je potřeba Google Maps API klíč

### Připojení k serveru
- Zkontrolujte, že server běží (zelený status "Připojeno")
- Obnovte stránku při problémech s připojením

## 🌐 Sdílení s kamarády

### Postup:
1. **Spusťte server** lokálně
2. **Použijte ngrok** nebo jinou tunnel službu
3. **Pošlete URL** kamarádovi (např. `https://abc123.ngrok.io`)
4. **Oba zapněte sledování** pro vzájemné vidění na mapě

### Příklad použití:
```
Řidič (Vy):
1. Spustíte server
2. Nabídnete jízdu Praha → Brno
3. Zapnete sledování GPS

Spolucestující (kamarád):
1. Otevře váš odkaz
2. Vyhledá jízdu Praha → Brno  
3. Zapne sledování GPS
4. Vidí vaši pozici na mapě v reálném čase
```

## 📊 Status indikátory

- **Připojeno** (zelená): Server komunikace funguje
- **Odpojeno** (červená): Problém s připojením
- **GPS: Aktivní**: Poloha se sleduje a odesílá
- **GPS: Neaktivní**: Sledování vypnuto

## 🔒 Bezpečnost

- **Nesdílejte** tunnel URL veřejně
- **Používejte** pouze s důvěryhodnými osobami
- **Vypněte sledování** když aplikaci nepoužíváte
- **Pozice se ukládají** pouze dočasně v paměti serveru

---

**Tip**: Pro nejlepší zážitek používejte aplikaci na mobilním zařízení s aktivním GPS! 📱🗺️