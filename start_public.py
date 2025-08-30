#!/usr/bin/env python3
import subprocess
import threading
import time
import requests
import json

# Import z hlavního app.py souboru
exec(open('app.py').read())
# Nyní máme přístup k app, socketio, init_db

def start_ngrok():
    """Spustí ngrok a získá veřejnou URL"""
    try:
        # Spustí ngrok na pozadí
        subprocess.Popen(['/snap/bin/ngrok', 'http', '5000'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Počká na spuštění ngrok
        time.sleep(5)
        
        # Získá veřejnou URL z ngrok API
        for attempt in range(10):
            try:
                response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
                tunnels = response.json()['tunnels']
                
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print("\n" + "="*60)
                    print("🚀 SPOLUJÍZDA SERVER SPUŠTĚN!")
                    print("="*60)
                    print(f"📱 Lokální přístup: http://127.0.0.1:5000")
                    print(f"🌍 Veřejný odkaz:   {public_url}")
                    print("="*60)
                    print("📤 POŠLETE TENTO ODKAZ KAMARÁDOVI:")
                    print(f"   {public_url}")
                    print("="*60)
                    print("⚠️  Pro zastavení stiskněte CTRL+C")
                    print("="*60 + "\n")
                    return
                    
            except:
                time.sleep(1)
                continue
                
        print("❌ Ngrok API nedostupné")
            
    except Exception as e:
        print(f"❌ Chyba při spouštění ngrok: {e}")

if __name__ == '__main__':
    # Zabije staré ngrok procesy
    subprocess.run(['pkill', '-f', 'ngrok'], stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    # Spustí ngrok
    subprocess.Popen(['/snap/bin/ngrok', 'http', '5000'])
    time.sleep(4)
    
    # Získá URL
    try:
        response = requests.get('http://127.0.0.1:4040/api/tunnels')
        url = response.json()['tunnels'][0]['public_url']
        print("\n" + "="*60)
        print("🚀 SPOLUJÍZDA SERVER SPUŠTĚN!")
        print("="*60)
        print(f"🌍 Veřejný odkaz: {url}")
        print("📤 POŠLETE TENTO ODKAZ KAMARÁDOVI:")
        print(f"   {url}")
        print("="*60 + "\n")
    except:
        print("❌ Ngrok chyba")
    
    # Spustí Flask server
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)