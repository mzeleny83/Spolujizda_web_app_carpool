#!/usr/bin/env python3
import requests
import json
import datetime

# Test notification system
BASE_URL = "https://spolujizda-645ec54e47aa.herokuapp.com"

def test_notifications():
    print("Testing notification system...")
    
    # 1. Test API endpoint directly
    user_name = "Pokus Pokus"
    url = f"{BASE_URL}/api/notifications/v361/{user_name}"
    
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            notifications = response.json()
            print(f"Found {len(notifications)} notifications")
            for notif in notifications:
                print(f"  - {notif['sender_name']}: {notif['message']}")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_notifications()