import requests
import json

# Test API endpointu pro vyhledávání uživatelů
base_url = "http://localhost:5000"

print("=== TEST API VYHLEDÁVÁNÍ ===\n")

# Test 1: Hledání pouze podle města
print("1. Test: Hledání pouze podle města 'Brno'")
try:
    response = requests.get(f"{base_url}/api/users/search?city=Brno")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"   Počet výsledků: {len(users)}")
        for user in users:
            print(f"   - {user['name']}: {user.get('home_city', 'N/A')}")
    else:
        print(f"   Chyba: {response.text}")
except Exception as e:
    print(f"   Chyba připojení: {e}")

print()

# Test 2: Hledání podle jména a města
print("2. Test: Hledání 'Miroslav' + město 'Brno'")
try:
    response = requests.get(f"{base_url}/api/users/search?q=Miroslav&city=Brno")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"   Počet výsledků: {len(users)}")
        for user in users:
            print(f"   - {user['name']}: {user.get('home_city', 'N/A')}")
    else:
        print(f"   Chyba: {response.text}")
except Exception as e:
    print(f"   Chyba připojení: {e}")

print()

# Test 3: Debug endpoint
print("3. Test: Debug všichni uživatelé")
try:
    response = requests.get(f"{base_url}/api/debug/users")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"   Počet uživatelů: {len(users)}")
        for user in users:
            print(f"   - {user['name']}: {user.get('home_city', 'NULL')}")
    else:
        print(f"   Chyba: {response.text}")
except Exception as e:
    print(f"   Chyba připojení: {e}")

print("\n=== KONEC TESTU ===")