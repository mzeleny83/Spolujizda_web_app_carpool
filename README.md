# Spolujízda - Aplikace pro sdílení jízd

Webová aplikace pro každodenní dojíždění a sdílení jízd mezi obyvateli města.

## Funkce

- 🌐 **Webová aplikace** - Responzivní design pro všechna zařízení
- 🚗 **Nabídka jízd** - Nabídněte volná místa ve svém autě
- 🔍 **Hledání jízd** - Najděte spolujízdu na vaší trase s GPS filtrováním
- 💬 **Real-time chat** - SocketIO komunikace mezi řidiči a spolucestujícími
- 📍 **Geolokace** - Automatické určení polohy a vzdálenostní vyhledávání
- 🔔 **Live notifikace** - Real-time upozornění na nové shody
- ⭐ **Hodnocení** - Systém hodnocení řidičů a spolucestujících
- 📱 **PWA ready** - Připraveno pro Progressive Web App

## Technologie

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python Flask + SocketIO
- **Databáze**: SQLite s optimalizovanými indexy
- **Real-time**: WebSocket komunikace
- **Deployment**: Heroku ready

## Instalace a spuštění

### Požadavky
- Python 3.8+
- pip package manager

### Lokální spuštění

```bash
# Klonování repozitáře
git clone <repository-url>
cd Spolujizda

# Instalace Python závislostí
pip install -r requirements.txt

# Spuštění serveru
python app.py
```

Server běží na: `http://localhost:8080`

### Heroku deployment

```bash
# Přihlášení do Heroku
heroku login

# Vytvoření Heroku aplikace
heroku create your-app-name

# Nasazení
git push heroku master
```

## Struktura projektu

```
├── static/                 # Statické soubory (CSS, JS)
│   ├── css/               # Styly aplikace
│   └── js/                # JavaScript funkce
├── templates/             # HTML šablony
├── lib/                   # Flutter kód (pro budoucí mobilní verzi)
├── app.py                 # Hlavní Flask aplikace
├── backend_search_api.py  # Pokročilé vyhledávání
├── requirements.txt       # Python závislosti
├── Procfile              # Heroku konfigurace
└── .python-version       # Python verze

```

## API Endpointy

### Uživatelé
- `POST /api/users/register` - Registrace uživatele
- `POST /api/users/login` - Přihlášení
- `GET /api/users/locations` - Aktuální polohy uživatelů
- `POST /api/users/search` - Vyhledávání uživatelů

### Jízdy
- `POST /api/rides/offer` - Nabídka jízdy
- `GET /api/rides/search` - Hledání jízd s GPS filtrováním
- `GET /api/rides/all` - Seznam všech jízd
- `POST /api/rides/recurring` - Pravidelné jízdy

### Rezervace a komunikace
- `POST /api/reservations/create` - Vytvoření rezervace
- `POST /api/messages/send` - Odeslání zprávy
- `POST /api/ratings/create` - Hodnocení uživatele

### Utility
- `GET /api/cities` - Seznam českých měst pro autocomplete
- `GET /api/status` - Status API serveru
- `GET /api/search/unified` - Jednotné vyhledávání

### WebSocket události
- `connect/disconnect` - Připojení/odpojení
- `update_location` - Aktualizace GPS polohy
- `join_ride_chat` - Připojení do chatu jízdy
- `send_chat_message` - Odeslání zprávy
- `share_live_location` - Sdílení live polohy

## Konfigurace

### Environment variables
```bash
PORT=8080                    # Port serveru (Heroku automaticky)
DATABASE_URL=sqlite:///...   # Databáze (volitelné)
```

### Databáze
Databáze se automaticky inicializuje při prvním spuštění s tabulkami:
- `users` - Uživatelé s hodnocením
- `rides` - Nabízené jízdy
- `reservations` - Rezervace míst
- `messages` - Chat zprávy
- `ratings` - Hodnocení uživatelů

## Funkce v provozu

✅ **Implementováno:**
- Registrace a přihlašování uživatelů
- Nabídka a vyhledávání jízd
- GPS vzdálenostní filtrování
- Real-time chat přes SocketIO
- Rezervace míst v jízdách
- Hodnocení řidičů
- Responzivní webový design
- Heroku deployment

🚧 **V přípravě:**
- Google Maps integrace
- Push notifikace
- Mobilní aplikace (Flutter)
- Platební systém

## Licence

MIT License

## Live Demo

🌐 **Heroku**: https://spolujizda-645ec54e47aa.herokuapp.com/

## Podpora

Pro technickou podporu nebo hlášení chyb vytvořte issue v tomto repozitáři.