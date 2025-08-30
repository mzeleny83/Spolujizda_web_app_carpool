#!/usr/bin/env python3
"""
HTTPS server pro Spolujízda aplikaci s automatickým SSL certifikátem
"""

import ssl
import os
import subprocess
import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
import socket

# Import původní aplikace
from app import app, socketio, init_db, create_search_routes

def generate_self_signed_cert():
    """Vytvoří self-signed SSL certifikát pro lokální vývoj"""
    cert_dir = Path("ssl_certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"
    
    if cert_file.exists() and key_file.exists():
        print("✅ SSL certifikáty již existují")
        return str(cert_file), str(key_file)
    
    print("🔐 Generuji SSL certifikát...")
    
    # Získá lokální IP adresu
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"
    
    # OpenSSL příkaz pro vytvoření certifikátu
    openssl_cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096", 
        "-keyout", str(key_file), "-out", str(cert_file),
        "-days", "365", "-nodes", "-subj", 
        f"/C=CZ/ST=Prague/L=Prague/O=Spolujizda/CN={local_ip}",
        "-addext", f"subjectAltName=DNS:localhost,DNS:{hostname},IP:127.0.0.1,IP:{local_ip}"
    ]
    
    try:
        subprocess.run(openssl_cmd, check=True, capture_output=True)
        print(f"✅ SSL certifikát vytvořen pro IP: {local_ip}")
        return str(cert_file), str(key_file)
    except subprocess.CalledProcessError as e:
        print(f"❌ Chyba při vytváření certifikátu: {e}")
        print("💡 Nainstalujte OpenSSL: sudo apt-get install openssl")
        return None, None
    except FileNotFoundError:
        print("❌ OpenSSL není nainstalován")
        print("💡 Nainstalujte OpenSSL: sudo apt-get install openssl")
        return None, None

def setup_https_headers(app):
    """Nastaví HTTPS hlavičky pro bezpečnost a mobilní kompatibilitu"""
    
    @app.after_request
    def add_security_headers(response):
        # HTTPS hlavičky
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Mobilní optimalizace
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # PWA podpora
        response.headers['Service-Worker-Allowed'] = '/'
        
        return response
    
    # Redirect HTTP na HTTPS
    @app.before_request
    def force_https():
        if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
            if request.method == 'GET':
                return redirect(request.url.replace('http://', 'https://'), code=301)

def get_local_ip():
    """Získá lokální IP adresu"""
    try:
        # Připojí se k externí adrese pro zjištění lokální IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def main():
    """Spustí HTTPS server"""
    print("🚀 Spouštím Spolujízda HTTPS server...")
    
    # Inicializace databáze
    try:
        init_db()
        print("✅ Databáze inicializována")
    except Exception as e:
        print(f"❌ Chyba databáze: {e}")
        return
    
    # Přidání pokročilých search API routes
    try:
        create_search_routes(app)
        print("✅ Pokročilé vyhledávání aktivováno")
    except Exception as e:
        print(f"⚠️ Varování - pokročilé vyhledávání: {e}")
    
    # Nastavení HTTPS hlaviček
    setup_https_headers(app)
    
    # Generování SSL certifikátu
    cert_file, key_file = generate_self_signed_cert()
    
    if not cert_file or not key_file:
        print("❌ Nelze vytvořit SSL certifikát, spouštím HTTP server...")
        print("🌐 Server běží na:")
        print("  📱 Lokální: http://localhost:8080")
        print("  🌍 Síťová: http://0.0.0.0:8080")
        socketio.run(app, debug=False, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
        return
    
    # Vytvoření SSL kontextu
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    
    # Získání IP adresy
    local_ip = get_local_ip()
    
    print("🔐 HTTPS server úspěšně nakonfigurován!")
    print("🌐 Server běží na:")
    print(f"  📱 Lokální: https://localhost:8443")
    print(f"  🌍 Síťová: https://{local_ip}:8443")
    print(f"  🔗 HTTP redirect: http://localhost:8080 -> https://localhost:8443")
    print("")
    print("📋 Instrukce pro přístup:")
    print("1. Otevřete https://localhost:8443 nebo https://{local_ip}:8443")
    print("2. Prohlížeč zobrazí varování o certifikátu - klikněte 'Pokračovat' nebo 'Advanced' -> 'Proceed'")
    print("3. Aplikace bude fungovat s HTTPS")
    print("")
    print("📱 Pro mobilní zařízení:")
    print(f"   Použijte: https://{local_ip}:8443")
    print("   Přijměte certifikát v prohlížeči")
    print("")
    print("🔴 Stiskněte Ctrl+C pro ukončení")
    
    try:
        # Spuštění HTTPS serveru
        socketio.run(
            app, 
            debug=False, 
            host='0.0.0.0', 
            port=8443,
            ssl_context=context,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n⚠️ Server ukončen uživatelem")
    except Exception as e:
        print(f"\n❌ Chyba serveru: {e}")
        print("💡 Zkuste spustit jako sudo nebo změnit port")

if __name__ == '__main__':
    main()