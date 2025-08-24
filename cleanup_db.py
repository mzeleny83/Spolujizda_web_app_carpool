#!/usr/bin/env python3
import requests
import sys

def cleanup_database():
    try:
        response = requests.post('http://localhost:5000/api/admin/cleanup')
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Databáze vyčištěna!")
            print(f"   Smazáno uživatelů bez města: {result['deleted_users']}")
            print(f"   Smazáno jízd s neplatnou cenou: {result['deleted_rides']}")
        else:
            print(f"❌ Chyba: {response.json().get('error', 'Neznámá chyba')}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server není spuštěn na http://localhost:5000")
    except Exception as e:
        print(f"❌ Chyba: {e}")

if __name__ == "__main__":
    cleanup_database()