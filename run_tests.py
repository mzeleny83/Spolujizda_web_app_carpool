#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

BASE_URL = 'http://localhost:8081'

def test_api():
    """Automatické testování API"""
    
    print("🧪 Spouštím automatické testy API...")
    
    # Test 1: Status API
    print("\n1️⃣ Test API status...")
    try:
        response = requests.get(f'{BASE_URL}/api/status')
        if response.status_code == 200:
            print("✅ API status - OK")
        else:
            print(f"❌ API status - CHYBA: {response.status_code}")
    except Exception as e:
        print(f"❌ API status - CHYBA: {e}")
    
    # Test 2: Registrace
    print("\n2️⃣ Test registrace...")
    test_user = {
        'name': 'Test Robot',
        'phone': '+420999999999',
        'email': 'robot@test.com',
        'password': 'test123',
        'password_confirm': 'test123'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/users/register', json=test_user)
        if response.status_code == 201:
            print("✅ Registrace - OK")
        elif response.status_code == 409:
            print("⚠️ Registrace - uživatel už existuje (OK)")
        else:
            print(f"❌ Registrace - CHYBA: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Registrace - CHYBA: {e}")
    
    # Test 3: Přihlášení
    print("\n3️⃣ Test přihlášení...")
    login_data = {
        'phone': '+420999999999',
        'password': 'test123'
    }
    
    user_id = None
    try:
        response = requests.post(f'{BASE_URL}/api/users/login', json=login_data)
        if response.status_code == 200:
            data = response.json()
            user_id = data.get('user_id')
            print(f"✅ Přihlášení - OK (user_id: {user_id})")
        else:
            print(f"❌ Přihlášení - CHYBA: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Přihlášení - CHYBA: {e}")
    
    # Test 4: Nabídka jízdy
    if user_id:
        print("\n4️⃣ Test nabídky jízdy...")
        ride_data = {
            'user_id': user_id,
            'from_location': 'Test Město A',
            'to_location': 'Test Město B',
            'departure_time': '2025-12-31T10:00',
            'available_seats': 2,
            'price_per_person': 100,
            'route_waypoints': []
        }
        
        try:
            response = requests.post(f'{BASE_URL}/api/rides/offer', json=ride_data)
            if response.status_code == 201:
                print("✅ Nabídka jízdy - OK")
            else:
                print(f"❌ Nabídka jízdy - CHYBA: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Nabídka jízdy - CHYBA: {e}")
    
    # Test 5: Vyhledávání jízd
    print("\n5️⃣ Test vyhledávání jízd...")
    try:
        response = requests.get(f'{BASE_URL}/api/rides/search?from=Praha')
        if response.status_code == 200:
            rides = response.json()
            print(f"✅ Vyhledávání - OK (nalezeno {len(rides)} jízd)")
        else:
            print(f"❌ Vyhledávání - CHYBA: {response.status_code}")
    except Exception as e:
        print(f"❌ Vyhledávání - CHYBA: {e}")
    
    # Test 6: Všechny jízdy
    print("\n6️⃣ Test všech jízd...")
    try:
        response = requests.get(f'{BASE_URL}/api/rides/all')
        if response.status_code == 200:
            rides = response.json()
            print(f"✅ Všechny jízdy - OK (celkem {len(rides)} jízd)")
        else:
            print(f"❌ Všechny jízdy - CHYBA: {response.status_code}")
    except Exception as e:
        print(f"❌ Všechny jízdy - CHYBA: {e}")
    
    print("\n🏁 Testy dokončeny!")

def test_web_pages():
    """Test načítání webových stránek"""
    
    print("\n🌐 Testování webových stránek...")
    
    pages = [
        ('/', 'Hlavní stránka'),
        ('/search', 'Vyhledávání'),
        ('/api/status', 'API Status')
    ]
    
    for url, name in pages:
        try:
            response = requests.get(f'{BASE_URL}{url}')
            if response.status_code == 200:
                print(f"✅ {name} - OK")
            else:
                print(f"❌ {name} - CHYBA: {response.status_code}")
        except Exception as e:
            print(f"❌ {name} - CHYBA: {e}")

def check_server():
    """Zkontroluje, jestli server běží"""
    
    print("🔍 Kontroluji server...")
    try:
        response = requests.get(f'{BASE_URL}/api/status', timeout=5)
        if response.status_code == 200:
            print("✅ Server běží")
            return True
        else:
            print("❌ Server neodpovídá správně")
            return False
    except Exception as e:
        print(f"❌ Server neběží: {e}")
        print("💡 Spusť server: python main_app.py")
        return False

if __name__ == '__main__':
    print("🚀 Automatické testování Spolujízda aplikace")
    print("=" * 50)
    
    if check_server():
        test_web_pages()
        test_api()
    else:
        print("\n⚠️ Server neběží. Spusť nejdříve server:")
        print("   python main_app.py")
        print("\nPak spusť testy znovu:")
        print("   python run_tests.py")