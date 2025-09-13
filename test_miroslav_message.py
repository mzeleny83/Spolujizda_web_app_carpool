#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://spolujizda-645ec54e47aa.herokuapp.com"

def send_miroslav_message():
    print("Sending message from Miroslav Zelený...")
    
    # Pošli zprávu do ride_id 34 (jízda uživatele "Pokus Pokus") od uživatele "Miroslav Zelený"
    message_data = {
        "ride_id": 34,
        "sender_name": "Miroslav Zelený",
        "message": "Ahoj, můžu se přidat na cestu?"
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
                    print(f"  - Created: {notif['created_at']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_miroslav_message()