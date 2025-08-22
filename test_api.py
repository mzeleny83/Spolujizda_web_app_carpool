import requests

# Test API endpoint
url = "http://localhost:8080/api/rides/search"
params = {"from": "Praha", "to": "Brno"}

try:
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Chyba: {e}")

# Test všechny jízdy
try:
    response = requests.get("http://localhost:8080/api/rides/all")
    print(f"\nVšechny jízdy - Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Chyba: {e}")