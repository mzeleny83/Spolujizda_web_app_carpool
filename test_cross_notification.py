#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://spolujizda-645ec54e47aa.herokuapp.com"

def test_cross_notification():
    print("Testing cross-user notifications...")
    
    # 1. Pošli zprávu od Miroslav Zelený
    message_data = {
        "ride_id": 34,  # Jízda uživatele "Pokus Pokus"
        "sender_name": "Miroslav Zelený",
        "message": "Nová zpráva pro test notifikací"
    }
    
    print("1. Sending message from Miroslav Zelený...")
    try:
        response = requests.post(f"{BASE_URL}/api/chat/send", 
                               json=message_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"   Status: {response.status_code}")
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            return
        
        print("   Message sent successfully!")
        
        # 2. Zkontroluj notifikace pro Pokus Pokus (příjemce)
        print("\n2. Checking notifications for 'Pokus Pokus' (recipient)...")
        notif_response = requests.get(f"{BASE_URL}/api/notifications/v361/Pokus Pokus")
        print(f"   Status: {notif_response.status_code}")
        
        if notif_response.status_code == 200:
            notifications = notif_response.json()
            print(f"   Found {len(notifications)} notifications for Pokus Pokus:")
            for notif in notifications:
                print(f"     - From: {notif['sender_name']}: '{notif['message']}'")
        
        # 3. Zkontroluj notifikace pro Miroslav Zelený (odesílatel)
        print("\n3. Checking notifications for 'Miroslav Zelený' (sender)...")
        sender_notif_response = requests.get(f"{BASE_URL}/api/notifications/v361/Miroslav Zelený")
        print(f"   Status: {sender_notif_response.status_code}")
        
        if sender_notif_response.status_code == 200:
            sender_notifications = sender_notif_response.json()
            print(f"   Found {len(sender_notifications)} notifications for Miroslav Zelený:")
            for notif in sender_notifications:
                print(f"     - From: {notif['sender_name']}: '{notif['message']}'")
        
        print("\n4. Summary:")
        print(f"   - Pokus Pokus should see notification from Miroslav Zelený: {'YES' if len(notifications) > 0 else 'NO'}")
        print(f"   - Miroslav Zelený should NOT see his own message: {'CORRECT' if len(sender_notifications) == 0 else 'WRONG'}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cross_notification()