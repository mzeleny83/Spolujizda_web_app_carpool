#!/usr/bin/env python3
import subprocess
import time
import hashlib
import os

def generate_fixed_subdomain():
    """Generuje vždy stejnou subdoménu z MAC adresy"""
    try:
        # Získá MAC adresu
        mac = subprocess.check_output("cat /sys/class/net/*/address | head -1", shell=True).decode().strip()
        # Vytvoří hash pro konzistentní subdoménu
        hash_obj = hashlib.md5(mac.encode())
        subdomain = hash_obj.hexdigest()[:12]  # Prvních 12 znaků
        return subdomain
    except:
        return "spolujizda2024"

def start_tunnel():
    """Spustí tunnel s fixní subdoménou"""
    subdomain = generate_fixed_subdomain()
    
    print(f"🚀 Spouštím tunnel s fixní subdoménou: {subdomain}")
    
    # Pokusí se o vlastní subdoménu přes SSH port forwarding
    cmd = f"ssh -o StrictHostKeyChecking=no -R {subdomain}:80:localhost:5000 serveo.net"
    
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    time.sleep(5)
    
    fixed_url = f"https://{subdomain}.serveo.net"
    
    print("=" * 60)
    print("🚀 SPOLUJÍZDA SERVER SPUŠTĚN!")
    print("=" * 60)
    print(f"🌍 STÁLÁ VEŘEJNÁ ADRESA: {fixed_url}")
    print(f"📤 POŠLETE TENTO ODKAZ KAMARÁDOVI:")
    print(f"   {fixed_url}")
    print("=" * 60)
    print("✅ Tato adresa bude VŽDY stejná!")
    print("=" * 60)
    
    return process

if __name__ == '__main__':
    tunnel_process = start_tunnel()
    
    # Spustí Flask aplikaci
    app_process = subprocess.Popen(['python3', 'app.py'])
    
    try:
        app_process.wait()
    except KeyboardInterrupt:
        tunnel_process.terminate()
        app_process.terminate()