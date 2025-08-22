#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import hashlib
from datetime import datetime, timedelta
import json

def create_test_data():
    """Vytvoří testovací data pro aplikaci"""
    
    conn = sqlite3.connect('spolujizda.db')
    c = conn.cursor()
    
    print("🧪 Vytváření testovacích dat...")
    
    # Vymaž existující testovací data
    c.execute("DELETE FROM users WHERE phone LIKE '+420111%' OR phone LIKE '+420222%' OR phone LIKE '+420333%'")
    c.execute("DELETE FROM rides WHERE user_id IN (SELECT id FROM users WHERE phone LIKE '+420111%' OR phone LIKE '+420222%' OR phone LIKE '+420333%')")
    
    # Testovací uživatelé
    test_users = [
        {
            'name': 'Jan Testovací',
            'phone': '+420111111111',
            'email': 'jan.test@example.com',
            'password': 'heslo123'
        },
        {
            'name': 'Marie Testovací',
            'phone': '+420222222222', 
            'email': 'marie.test@example.com',
            'password': 'heslo456'
        },
        {
            'name': 'Petr Testovací',
            'phone': '+420333333333',
            'email': 'petr.test@example.com', 
            'password': 'heslo789'
        }
    ]
    
    user_ids = []
    
    # Vytvoř testovací uživatele
    for user in test_users:
        password_hash = hashlib.sha256(user['password'].encode()).hexdigest()
        
        c.execute('''INSERT INTO users (name, phone, email, password_hash, rating) 
                     VALUES (?, ?, ?, ?, ?)''',
                 (user['name'], user['phone'], user['email'], password_hash, 5.0))
        
        user_ids.append(c.lastrowid)
        print(f"✅ Vytvořen uživatel: {user['name']} ({user['phone']})")
    
    # Testovací jízdy
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    day_after = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
    today_evening = datetime.now().replace(hour=18, minute=0).strftime('%Y-%m-%dT%H:%M')
    
    test_rides = [
        {
            'user_id': user_ids[0],
            'from_location': 'Praha',
            'to_location': 'Brno',
            'departure_time': tomorrow.replace('T', 'T08:'),
            'available_seats': 3,
            'price_per_person': 250,
            'route_waypoints': json.dumps([
                {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'},
                {'lat': 49.1951, 'lng': 16.6068, 'name': 'Brno centrum'}
            ])
        },
        {
            'user_id': user_ids[1],
            'from_location': 'Brno',
            'to_location': 'Ostrava', 
            'departure_time': day_after.replace('T', 'T15:'),
            'available_seats': 2,
            'price_per_person': 200,
            'route_waypoints': json.dumps([
                {'lat': 49.1951, 'lng': 16.6068, 'name': 'Brno centrum'},
                {'lat': 49.8209, 'lng': 18.2625, 'name': 'Ostrava centrum'}
            ])
        },
        {
            'user_id': user_ids[2],
            'from_location': 'Plzeň',
            'to_location': 'Praha',
            'departure_time': today_evening,
            'available_seats': 1,
            'price_per_person': 150,
            'route_waypoints': json.dumps([
                {'lat': 49.7384, 'lng': 13.3736, 'name': 'Plzeň centrum'},
                {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'}
            ])
        },
        {
            'user_id': user_ids[0],
            'from_location': 'Liberec',
            'to_location': 'Hradec Králové',
            'departure_time': tomorrow.replace('T', 'T12:'),
            'available_seats': 2,
            'price_per_person': 180,
            'route_waypoints': json.dumps([
                {'lat': 50.7663, 'lng': 15.0543, 'name': 'Liberec centrum'},
                {'lat': 50.2103, 'lng': 15.8327, 'name': 'Hradec Králové centrum'}
            ])
        },
        {
            'user_id': user_ids[1],
            'from_location': 'Olomouc',
            'to_location': 'Zlín',
            'departure_time': day_after.replace('T', 'T09:'),
            'available_seats': 3,
            'price_per_person': 120,
            'route_waypoints': json.dumps([
                {'lat': 49.5938, 'lng': 17.2509, 'name': 'Olomouc centrum'},
                {'lat': 49.2265, 'lng': 17.6679, 'name': 'Zlín centrum'}
            ])
        }
    ]
    
    # Vytvoř testovací jízdy
    for ride in test_rides:
        c.execute('''INSERT INTO rides 
                     (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (ride['user_id'], ride['from_location'], ride['to_location'], 
                  ride['departure_time'], ride['available_seats'], ride['price_per_person'], ride['route_waypoints']))
        
        print(f"✅ Vytvořena jízda: {ride['from_location']} → {ride['to_location']} ({ride['departure_time']})")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Testovací data úspěšně vytvořena!")
    print("\n📋 Testovací účty:")
    print("1. Jan Testovací - +420111111111 - heslo123")
    print("2. Marie Testovací - +420222222222 - heslo456") 
    print("3. Petr Testovací - +420333333333 - heslo789")
    print("\n🚗 Vytvořeno 5 testovacích jízd")
    print("\n▶️  Spusť server: python main_app.py")
    print("🌐 Otevři: http://localhost:8081")

if __name__ == '__main__':
    create_test_data()