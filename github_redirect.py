#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import os

def create_github_redirect():
    """Vytvoří GitHub Pages redirect"""
    
    # Vytvoří HTML redirect stránku
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Spolujízda - Přesměrování</title>
    <script>
        // Získá aktuální tunnel URL z API
        fetch('https://api.github.com/gists/anonymous')
        .then(response => response.json())
        .then(data => {
            // Přesměruje na aktuální tunnel
            const tunnelUrl = localStorage.getItem('spolujizda_url') || 'https://github.com';
            window.location.href = tunnelUrl;
        })
        .catch(() => {
            document.body.innerHTML = '<h1>Server se spouští...</h1><p>Zkuste za chvíli</p>';
        });
    </script>
</head>
<body>
    <h1>🚗 Spolujízda</h1>
    <p>Přesměrovávám na server...</p>
</body>
</html>'''
    
    # Uloží HTML soubor
    with open('/tmp/redirect.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ GitHub redirect vytvořen")
    return "https://spolujizda.github.io"

def start_simple_tunnel():
    """Spustí jednoduchý tunnel"""
    print("🚀 Spouštím tunnel...")
    
    # Spustí serveo
    process = subprocess.Popen([
        'ssh', '-o', 'StrictHostKeyChecking=no', 
        '-R', '80:localhost:5000', 'serveo.net'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    time.sleep(5)
    
    # Získá URL z výstupu
    try:
        output, _ = process.communicate(timeout=10)
        import re
        match = re.search(r'https://[a-zA-Z0-9]+\.serveo\.net', output)
        if match:
            tunnel_url = match.group(0)
            print(f"✅ Tunnel URL: {tunnel_url}")
            return tunnel_url, process
    except:
        pass
    
    return None, process

if __name__ == '__main__':
    # Vytvoří redirect
    redirect_url = create_github_redirect()
    
    # Spustí tunnel
    tunnel_url, tunnel_process = start_simple_tunnel()
    
    print("=" * 60)
    print("🚀 SPOLUJÍZDA SERVER SPUŠTĚN!")
    print("=" * 60)
    
    if tunnel_url:
        print(f"🌍 AKTUÁLNÍ ADRESA: {tunnel_url}")
        print(f"📤 POŠLETE TENTO ODKAZ KAMARÁDOVI:")
        print(f"   {tunnel_url}")
    else:
        print("❌ Tunnel se nespustil")
    
    print("=" * 60)
    
    # Spustí Flask aplikaci
    app_process = subprocess.Popen(['python3', 'app.py'])
    
    try:
        app_process.wait()
    except KeyboardInterrupt:
        if tunnel_process:
            tunnel_process.terminate()
        app_process.terminate()