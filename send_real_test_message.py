#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://spolujizda-645ec54e47aa.herokuapp.com"

def send_test_message():
    print("Sending test message...")
    
    # Pošli zprávu do ride_id 34 (jízda uživatele "Pokus Pokus") od uživatele "Jan Novák"
    message_data = {
        "ride_id": 34,
        "sender_name": "Jan Novák",
        "message": "Ahoj, mám zájem o spolujízdu!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat/send", 
                               json=message_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Message send status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("Message sent successfully!")
            
            # Počkej chvilku a zkontroluj notifikace pro "Pokus Pokus"
            import time
            time.sleep(2)
            
            print("\nChecking notifications for 'Pokus Pokus'...")
            notif_response = requests.get(f"{BASE_URL}/api/notifications/v361/Pokus Pokus")
            print(f"Notifications status: {notif_response.status_code}")
            print(f"Notifications: {notif_response.text}")
            
            if notif_response.status_code == 200:
                notifications = notif_response.json()
                print(f"Found {len(notifications)} notifications!")
                for notif in notifications:
                    print(f"  - From: {notif['sender_name']}")
                    print(f"  - Message: {notif['message']}")
                    print(f"  - Ride ID: {notif['ride_id']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_test_message()