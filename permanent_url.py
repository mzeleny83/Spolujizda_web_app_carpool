#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import os

def get_current_tunnel():
    """Získá aktuální tunnel URL"""
    try:
        with open('/tmp/current_tunnel.txt', 'r') as f:
            return f.read().strip()
    except:
        return None

def update_redirect(tunnel_url):
    """Aktualizuje redirect na is.gd"""
    try:
        # Vytvoří krátký odkaz který přesměruje na aktuální tunnel
        response = requests.post('https://is.gd/create.php', data={
            'format': 'simple',
            'url': tunnel_url,
            'shorturl': 'spolujizda2024'
        })
        
        if response.status_code == 200:
            short_url = response.text.strip()
            print(f"✅ Redirect aktualizován: {short_url}")
            return short_url
        else:
            print("❌ Chyba při vytváření redirectu")
            return None
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return None

def start_tunnel():
    """Spustí tunnel a aktualizuje redirect"""
    print("🚀 Spouštím tunnel...")
    
    # Spustí serveo
    process = subprocess.Popen([
        'ssh', '-o', 'StrictHostKeyChecking=no', 
        '-R', '80:localhost:5000', 'serveo.net'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    time.sleep(5)
    
    # Získá URL z výstupu
    try:
        output = process.stdout.read()
        import re
        match = re.search(r'https://[a-zA-Z0-9]+\.serveo\.net', output)
        if match:
            tunnel_url = match.group(0)
            
            # Uloží aktuální URL
            with open('/tmp/current_tunnel.txt', 'w') as f:
                f.write(tunnel_url)
            
            # Aktualizuje redirect
            redirect_url = update_redirect(tunnel_url)
            
            print("=" * 60)
            print("🚀 SPOLUJÍZDA SERVER SPUŠTĚN!")
            print("=" * 60)
            print(f"🌍 STÁLÝ ODKAZ: https://is.gd/spolujizda2024")
            print(f"📤 POŠLETE TENTO ODKAZ KAMARÁDOVI:")
            print(f"   https://is.gd/spolujizda2024")
            print("=" * 60)
            print("✅ Tento odkaz bude VŽDY fungovat!")
            print("=" * 60)
            
            return True
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return False

if __name__ == '__main__':
    start_tunnel()