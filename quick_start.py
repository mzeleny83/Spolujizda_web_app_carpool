#!/usr/bin/env python3
"""
Rychlé spuštění Spolujízda aplikace s automatickými opravami
"""

import os
import sys
import subprocess
import socket
from pathlib import Path

def check_dependencies():
    """Zkontroluje a nainstaluje závislosti"""
    print("📦 Kontroluji Python závislosti...")
    
    required_packages = ['flask', 'flask_cors', 'flask_socketio', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Chybí balíčky: {', '.join(missing_packages)}")
        print("📥 Instaluji závislosti...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True, capture_output=True)
            print("✅ Závislosti nainstalovány")
        except subprocess.CalledProcessError as e:
            print(f"❌ Chyba při instalaci: {e}")
            return False
    else:
        print("✅ Všechny závislosti jsou k dispozici")
    
    return True

def check_openssl():
    """Zkontroluje dostupnost OpenSSL"""
    try:
        subprocess.run(['openssl', 'version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_local_ip():
    """Získá lokální IP adresu"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def main():
    """Hlavní funkce pro spuštění aplikace"""
    print("🚀 Spolujízda - Rychlé spuštění")
    print("=" * 50)
    
    # Kontrola závislostí
    if not check_dependencies():
        print("❌ Nelze pokračovat bez závislostí")
        return
    
    # Získání IP adresy
    local_ip = get_local_ip()
    
    # Kontrola OpenSSL pro HTTPS
    has_openssl = check_openssl()
    
    if has_openssl:
        print("🔐 OpenSSL dostupný - spouštím HTTPS server")
        print(f"🌐 Aplikace bude dostupná na:")
        print(f"   📱 Lokální: https://localhost:8443")
        print(f"   🌍 Síťová: https://{local_ip}:8443")
        print("")
        print("📋 Instrukce pro přátele:")
        print(f"1. Otevřete: https://{local_ip}:8443")
        print("2. Přijměte SSL certifikát v prohlížeči")
        print("3. Aplikace bude fungovat")
        print("")
        print("🔴 Stiskněte Ctrl+C pro ukončení")
        print("=" * 50)
        
        try:
            from https_server import main as https_main
            https_main()
        except ImportError:
            print("❌ Chyba při importu HTTPS serveru")
            fallback_to_http(local_ip)
        except Exception as e:
            print(f"❌ Chyba HTTPS serveru: {e}")
            fallback_to_http(local_ip)
    else:
        print("⚠️ OpenSSL není dostupný - spouštím HTTP server")
        fallback_to_http(local_ip)

def fallback_to_http(local_ip):
    """Záložní spuštění HTTP serveru"""
    print("🌐 HTTP server - aplikace bude dostupná na:")
    print(f"   📱 Lokální: http://localhost:8080")
    print(f"   🌍 Síťová: http://{local_ip}:8080")
    print("")
    print("⚠️ Upozornění: HTTP server může mít omezené funkce na mobilních zařízeních")
    print("💡 Pro plnou funkcionalnost nainstalujte OpenSSL: sudo apt-get install openssl")
    print("")
    print("🔴 Stiskněte Ctrl+C pro ukončení")
    print("=" * 50)
    
    try:
        from app import app, socketio, init_db, create_search_routes
        from mobile_fix import add_mobile_fixes
        
        # Inicializace
        init_db()
        create_search_routes(app)
        add_mobile_fixes(app)
        
        # Spuštění HTTP serveru
        socketio.run(app, debug=False, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
        
    except Exception as e:
        print(f"❌ Chyba při spuštění: {e}")
        print("💡 Zkuste spustit přímo: python3 app.py")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Server ukončen uživatelem")
        print("✅ Děkujeme za použití Spolujízda!")
    except Exception as e:
        print(f"\n❌ Neočekávaná chyba: {e}")
        print("💡 Zkuste spustit přímo: python3 app.py")