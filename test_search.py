import requests

# Test search API
url = "http://localhost:8080/api/rides/search"
params = {"from": "Praha"}

try:
    response = requests.get(url, params=params)
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Chyba: {e}")