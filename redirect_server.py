#!/usr/bin/env python3
from flask import Flask, redirect, request
import subprocess
import re
import time
import threading

app = Flask(__name__)
current_tunnel_url = None

def update_tunnel():
    """Aktualizuje tunnel URL"""
    global current_tunnel_url
    try:
        # Spustí serveo a získá URL
        process = subprocess.Popen([
            'ssh', '-o', 'StrictHostKeyChecking=no', 
            '-R', '80:localhost:5001', 'serveo.net'  # Port 5001 pro redirect
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        time.sleep(5)
        output, _ = process.communicate(timeout=10)
        
        match = re.search(r'https://[a-zA-Z0-9]+\.serveo\.net', output)
        if match:
            current_tunnel_url = match.group(0)
            print(f"✅ Tunnel aktualizován: {current_tunnel_url}")
            return True
    except Exception as e:
        print(f"❌ Chyba tunnel: {e}")
    return False

@app.route('/')
def redirect_to_tunnel():
    """Přesměruje na aktuální tunnel"""
    if current_tunnel_url:
        return redirect(current_tunnel_url)
    else:
        return "Server se spouští, zkuste za chvíli...", 503

if __name__ == '__main__':
    # Spustí tunnel v pozadí
    threading.Thread(target=update_tunnel, daemon=True).start()
    time.sleep(2)
    
    print("🚀 REDIRECT SERVER SPUŠTĚN!")
    print("🌍 STÁLÁ ADRESA: http://localhost:8080")
    
    # Spustí redirect server
    app.run(host='0.0.0.0', port=8080, debug=False)