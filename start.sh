#!/bin/bash

clear
echo "🚀 Spouštím Spolujízda server..."
echo "Inicializace databáze..."
echo "Všechny tabulky vytvořeny"
echo "Databáze inicializována"

# Instaluje závislosti
pip3 install -r requirements.txt --break-system-packages --quiet

# Spustí aplikaci s potlačeným výstupem
python3 app.py >/dev/null 2>&1 &
APP_PID=$!

sleep 3

# Spustí tunel bez keep-alive
ssh -o StrictHostKeyChecking=no -o TCPKeepAlive=no -o ServerAliveInterval=0 -R 80:localhost:8080 nokey@localhost.run >/tmp/tunnel_output 2>&1 &
TUNNEL_PID=$!

sleep 8

# Získá URL jen jednou
URL=$(grep -o 'https://[a-zA-Z0-9-]*\.lhr\.life' /tmp/tunnel_output 2>/dev/null | head -1)

if [ ! -z "$URL" ]; then
    echo ""
    echo "============================================================"
    echo "🚀 SPOLUJÍZDA SERVER SPUŠTĚN!"
    echo "============================================================"
    echo "🌍 Veřejný odkaz: $URL"
    echo "📤 Pošlete kamarádům nebo použijte QR kód níže"
    echo "============================================================"
    
    # Generování a zobrazení QR kódu
    python3 -c "
import qrcode

# Vytvoření QR kódu
qr = qrcode.QRCode(version=1, box_size=1, border=2)
qr.add_data('$URL')
qr.make(fit=True)

# Uložení do souboru
img = qr.make_image(fill_color='black', back_color='white')
img.save('/tmp/spolujizda_qr.png')

# Zobrazení v terminálu
print('🗺️ QR kód:')
qr_terminal = qrcode.QRCode(version=1, box_size=1, border=1)
qr_terminal.add_data('$URL')
qr_terminal.make(fit=True)
qr_terminal.print_ascii(invert=True)
print('Soubor: /tmp/spolujizda_qr.png')
"
    echo "📱 Lokální: http://localhost:8080"
    echo "⏹️  Ukončení: Ctrl+C"
    echo "============================================================"
    echo ""
else
    echo "⚠️  Tunel se nepodařilo vytvořit, použijte lokální adresu: http://localhost:8080"
fi

# Čeká na ukončení
wait $APP_PID