# 🚀 Jak spustit Spolujízda aplikaci

## ✅ Backend server je spuštěný!
Server běží na: http://127.0.0.1:5000

## 📱 Spuštění Flutter aplikace

### 1. Instalace Flutter (pokud nemáte)
```bash
# Stáhněte Flutter z: https://flutter.dev/docs/get-started/install
# Nebo použijte snap:
sudo snap install flutter --classic
```

### 2. Spuštění aplikace
```bash
cd /home/win/Desktop/Programování/AI-Editor/Projekt

# Instalace závislostí
flutter pub get

# Spuštění na webu (nejjednodušší)
flutter run -d chrome

# Nebo spuštění na Android
flutter run -d android
```

## 🔧 Pokud Flutter nefunguje

### Alternativa 1: Použijte online Flutter editor
1. Jděte na: https://dartpad.dev
2. Zkopírujte obsah z `lib/main.dart`
3. Spusťte online

### Alternativa 2: Instalace Flutter přes snap
```bash
sudo snap install flutter --classic
flutter doctor
```

### Alternativa 3: Ruční instalace
```bash
# Stáhněte Flutter SDK
wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.16.0-stable.tar.xz

# Rozbalte
tar xf flutter_linux_3.16.0-stable.tar.xz

# Přidejte do PATH
export PATH="$PATH:`pwd`/flutter/bin"

# Ověřte instalaci
flutter doctor
```

## 🌐 Testování backend serveru

Server běží správně! Můžete testovat:

```bash
# Test základní route
curl http://127.0.0.1:5000/

# Test registrace
curl -X POST http://127.0.0.1:5000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@test.com","password":"123456"}'

# Test přihlášení
curl -X POST http://127.0.0.1:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
```

## 📋 Stav projektu

✅ Backend server - FUNGUJE  
❓ Flutter aplikace - potřebuje Flutter SDK  
✅ Databáze - automaticky se vytvoří  
✅ API endpointy - připravené  

Jakmile nainstalujete Flutter, aplikace bude plně funkční!