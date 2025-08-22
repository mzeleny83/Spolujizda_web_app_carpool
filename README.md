# Spolujízda - Aplikace pro sdílení jízd

Mobilní a webová aplikace pro každodenní dojíždění a sdílení jízd mezi obyvateli města.

## Funkce

- 📱 **Multiplatformní** - Android, iOS, Web
- 🚗 **Nabídka jízd** - Nabídněte volná místa ve svém autě
- 🔍 **Hledání jízd** - Najděte spolujízdu na vaší trase
- 💬 **Chat** - Komunikace mezi řidiči a spolucestujícími
- 📍 **Geolokace** - Automatické určení polohy
- 🔔 **Notifikace** - Upozornění na nové shody

## Technologie

- **Frontend**: Flutter (Dart)
- **Backend**: Python Flask
- **Databáze**: SQLite
- **Mapy**: Google Maps API
- **Notifikace**: Firebase Cloud Messaging

## Instalace a spuštění

### Požadavky
- Flutter SDK 3.0+
- Python 3.8+
- Android Studio (pro Android)
- Xcode (pro iOS)

### Spuštění Flutter aplikace

```bash
# Instalace závislostí
flutter pub get

# Spuštění na webu
flutter run -d chrome

# Spuštění na Android
flutter run -d android

# Spuštění na iOS
flutter run -d ios
```

### Spuštění backend serveru

```bash
# Instalace Python závislostí
pip install -r requirements.txt

# Spuštění serveru
python app.py
```

## Struktura projektu

```
├── lib/                    # Flutter aplikace
│   ├── screens/           # Obrazovky aplikace
│   └── main.dart         # Hlavní soubor
├── web/                   # Webová verze
├── android/              # Android konfigurace
├── ios/                  # iOS konfigurace
├── app.py               # Python backend
└── requirements.txt     # Python závislosti
```

## API Endpointy

- `POST /api/users/register` - Registrace uživatele
- `POST /api/users/login` - Přihlášení
- `POST /api/rides/offer` - Nabídka jízdy
- `GET /api/rides/search` - Hledání jízd
- `POST /api/matches` - Párování jízd

## Licence

MIT License