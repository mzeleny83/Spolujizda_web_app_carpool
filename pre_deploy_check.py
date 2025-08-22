#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3

def pre_deploy_check():
    """Kontrola před nasazením do produkce"""
    
    print("🔍 Kontrola před nasazením...")
    
    checks = []
    
    # 1. Soubory existují
    required_files = [
        'main_app.py',
        'requirements.txt', 
        'Procfile',
        'runtime.txt',
        'templates/app.html'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            checks.append(f"✅ {file} - OK")
        else:
            checks.append(f"❌ {file} - CHYBÍ")
    
    # 2. Databáze funguje
    try:
        conn = sqlite3.connect('spolujizda.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users')
        user_count = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM rides') 
        ride_count = c.fetchone()[0]
        conn.close()
        checks.append(f"✅ Databáze - OK ({user_count} uživatelů, {ride_count} jízd)")
    except Exception as e:
        checks.append(f"❌ Databáze - CHYBA: {e}")
    
    # 3. Port konfigurace
    with open('main_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'os.environ.get(\'PORT\'' in content:
            checks.append("✅ PORT konfigurace - OK")
        else:
            checks.append("❌ PORT konfigurace - CHYBÍ")
    
    # 4. Debug vypnutý
    if 'debug=False' in content:
        checks.append("✅ Debug vypnutý - OK")
    else:
        checks.append("⚠️ Debug zapnutý - DOPORUČUJI VYPNOUT")
    
    # Výsledky
    print("\n📋 Výsledky kontroly:")
    for check in checks:
        print(check)
    
    # Celkové hodnocení
    errors = [c for c in checks if c.startswith('❌')]
    warnings = [c for c in checks if c.startswith('⚠️')]
    
    print(f"\n📊 Shrnutí:")
    print(f"✅ OK: {len(checks) - len(errors) - len(warnings)}")
    print(f"⚠️ Varování: {len(warnings)}")
    print(f"❌ Chyby: {len(errors)}")
    
    if len(errors) == 0:
        print("\n🚀 APLIKACE JE PŘIPRAVENÁ K NASAZENÍ!")
        print("\n💡 Doporučené platformy:")
        print("   1. Railway.app (nejjednodušší)")
        print("   2. Render.com (zdarma)")
        print("   3. Heroku (klasika)")
    else:
        print("\n⚠️ OPRAV CHYBY PŘED NASAZENÍM!")
    
    return len(errors) == 0

if __name__ == '__main__':
    pre_deploy_check()