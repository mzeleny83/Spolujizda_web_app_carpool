#!/bin/bash

# Spolujízda HTTPS Server Starter
# Automatické spuštění HTTPS serveru s SSL certifikátem

echo "🚀 Spouštím Spolujízda HTTPS server..."

# Kontrola Python závislostí
echo "📦 Kontroluji závislosti..."
if ! python3 -c "import flask, flask_cors, flask_socketio" 2>/dev/null; then
    echo "❌ Chybí Python závislosti. Instaluji..."
    pip3 install -r requirements.txt
fi

# Kontrola OpenSSL
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL není nainstalován"
    echo "💡 Nainstalujte: sudo apt-get install openssl"
    echo "🔄 Spouštím HTTP server místo HTTPS..."
    python3 app.py
    exit 1
fi

# Vytvoření SSL certifikátu pokud neexistuje
if [ ! -f "ssl_certs/cert.pem" ] || [ ! -f "ssl_certs/key.pem" ]; then
    echo "🔐 Vytvářím SSL certifikát..."
    mkdir -p ssl_certs
    
    # Získání lokální IP adresy
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP="127.0.0.1"
    fi
    
    # Vytvoření self-signed certifikátu
    openssl req -x509 -newkey rsa:4096 \
        -keyout ssl_certs/key.pem -out ssl_certs/cert.pem \
        -days 365 -nodes \
        -subj "/C=CZ/ST=Prague/L=Prague/O=Spolujizda/CN=$LOCAL_IP" \
        -addext "subjectAltName=DNS:localhost,DNS:$(hostname),IP:127.0.0.1,IP:$LOCAL_IP"
    
    if [ $? -eq 0 ]; then
        echo "✅ SSL certifikát vytvořen pro IP: $LOCAL_IP"
    else
        echo "❌ Chyba při vytváření certifikátu"
        echo "🔄 Spouštím HTTP server místo HTTPS..."
        python3 app.py
        exit 1
    fi
fi

# Spuštění HTTPS serveru
echo "🌐 Spouštím HTTPS server..."
echo "📱 Přístupné na:"
echo "   https://localhost:8443"
echo "   https://$(hostname -I | awk '{print $1}'):8443"
echo ""
echo "📋 Instrukce:"
echo "1. Otevřete odkaz v prohlížeči"
echo "2. Přijměte SSL certifikát (klikněte 'Pokračovat' nebo 'Advanced' -> 'Proceed')"
echo "3. Aplikace bude fungovat s HTTPS"
echo ""
echo "🔴 Stiskněte Ctrl+C pro ukončení"

# Spuštění Python HTTPS serveru
python3 https_server.py

echo "✅ Server ukončen"