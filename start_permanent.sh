#!/bin/bash

echo "🚀 Spouštím se STÁLOU adresou..."

# Serveo s registrovaným klíčem
ssh -i ~/.ssh/serveo_key -o StrictHostKeyChecking=no -R spolujizda:80:localhost:5000 serveo.net 2>&1 | tee /tmp/serveo_output &
SSH_PID=$!
sleep 5

echo ""
echo "============================================================"
echo "🚀 SPOLUJÍZDA SERVER SPUŠTĚN!"
echo "============================================================"
echo "🌍 STÁLÁ ADRESA: https://spolujizda.serveo.net"
echo "📤 POŠLETE TENTO ODKAZ KAMARÁDOVI:"
echo "   https://spolujizda.serveo.net"
echo "============================================================"
echo "✅ Tato adresa bude VŽDY STEJNÁ!"
echo "============================================================"
echo ""

# Spustí Flask server
python3 app.py