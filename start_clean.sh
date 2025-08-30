#!/bin/bash

echo "🚀 Spouštím Spolujízda server..."

# Instaluje závislosti
pip3 install -r requirements.txt --break-system-packages --quiet >/dev/null 2>&1

# Spustí aplikaci na pozadí s potlačeným výstupem
python3 app.py >/dev/null 2>&1 &
APP_PID=$!

sleep 3

# Spustí tunel s potlačeným výstupem
ssh -o StrictHostKeyChecking=no -o TCPKeepAlive=no -o ServerAliveInterval=0 -R 80:localhost:8080 nokey@localhost.run 2>/tmp/tunnel_output >/dev/null &
TUNNEL_PID=$!

sleep 8

# Získá URL z chybového výstupu
URL=$(grep -o 'https://[a-zA-Z0-9-]*\.lhr\.life' /tmp/tunnel_output 2>/dev/null | head -1)

echo ""
echo "============================================================"
echo "🚀 SPOLUJÍZDA SERVER SPUŠTĚN!"
echo "============================================================"

if [ ! -z "$URL" ]; then
    echo "🌍 VEŘEJNÁ ADRESA: $URL"
    echo "📤 ODKAZ PRO KAMARÁDY: $URL"
else
    echo "⚠️  Tunel se nepodařilo vytvořit"
fi

echo "============================================================"
echo "📱 Lokální: http://localhost:8080"
echo "⏹️  Ukončení: Ctrl+C"
echo "============================================================"
echo ""

# Čeká na ukončení
wait $APP_PID