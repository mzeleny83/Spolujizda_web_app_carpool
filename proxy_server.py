#!/usr/bin/env python3
from flask import Flask, request, Response
import requests
import subprocess
import re
import time
import threading
import os

app = Flask(__name__)
current_target = "http://localhost:5000"

def update_target():
    """Neustále aktualizuje cílový server"""
    global current_target
    while True:
        try:
            # Test jestli lokální server běží
            response = requests.get("http://localhost:5000", timeout=2)
            if response.status_code == 200:
                current_target = "http://localhost:5000"
        except:
            current_target = "http://localhost:5000"
        time.sleep(10)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    """Proxy všechny požadavky na lokální server"""
    try:
        url = f"{current_target}/{path}"
        
        # Přepošle požadavek
        if request.method == 'GET':
            resp = requests.get(url, params=request.args, headers=dict(request.headers), timeout=10)
        elif request.method == 'POST':
            resp = requests.post(url, data=request.get_data(), headers=dict(request.headers), timeout=10)
        else:
            resp = requests.request(request.method, url, data=request.get_data(), headers=dict(request.headers), timeout=10)
        
        # Vrátí odpověď
        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
    except Exception as e:
        return f"Server nedostupný: {e}", 503

if __name__ == '__main__':
    # Spustí monitoring v pozadí
    threading.Thread(target=update_target, daemon=True).start()
    
    print("🚀 PROXY SERVER SPUŠTĚN!")
    print("🌍 STÁLÁ ADRESA: http://proxy.spolujizda.local")
    
    # Spustí proxy na portu 3000
    app.run(host='0.0.0.0', port=3000, debug=False)