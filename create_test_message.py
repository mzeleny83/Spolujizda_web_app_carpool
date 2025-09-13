#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://spolujizda-645ec54e47aa.herokuapp.com"

def create_test_message():
    print("Creating test message...")
    
    # Pošli zprávu do ride_id 1 od uživatele "Test User"
    message_data = {
        "ride_id": 1,
        "sender_name": "Test User",
        "message": "Testovací zpráva pro notifikace"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat/send", 
                               json=message_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Message send status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("Message sent successfully!")
            
            # Nyní zkontroluj notifikace
            print("\nChecking notifications...")
            notif_response = requests.get(f"{BASE_URL}/api/notifications/v361/Pokus Pokus")
            print(f"Notifications: {notif_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_test_message()