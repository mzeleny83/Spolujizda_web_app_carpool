#!/usr/bin/env python3
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
import traceback

DATABASE = 'spolujizda.db'

def add_test_data():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Vymaž existující data
        c.execute('DELETE FROM rides')
        c.execute('DELETE FROM users WHERE id > 0')
        
        # Přidej testovací uživatele
        users = [
            ('Jan Novák', '+420123456789', 'jan@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.8),
            ('Marie Svobodová', '+420987654321', 'marie@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.9),
            ('Petr Dvořák', '+420555666777', 'petr@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.7),
            ('Anna Nováková', '+420111222333', 'anna@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 5.0),
            ('Tomáš Procházka', '+420444555666', 'tomas@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.6)
        ]
        
        for user in users:
            c.execute('INSERT INTO users (name, phone, email, password_hash, rating) VALUES (?, ?, ?, ?, ?)', user)
        
        # Přidej testovací jízdy s GPS souřadnicemi
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        
        rides = [
            # Praha - Brno
            (1, 'Praha', 'Brno', tomorrow, 3, 300, json.dumps([
                {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'},
                {'lat': 49.1951, 'lng': 16.6068, 'name': 'Brno centrum'}
            ])),
            # Ostrava - Praha
            (2, 'Ostrava', 'Praha', tomorrow, 2, 400, json.dumps([
                {'lat': 49.8209, 'lng': 18.2625, 'name': 'Ostrava centrum'},
                {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'}
            ])),
            # Plzeň - České Budějovice
            (3, 'Plzeň', 'České Budějovice', tomorrow, 4, 250, json.dumps([
                {'lat': 49.7384, 'lng': 13.3736, 'name': 'Plzeň centrum'},
                {'lat': 48.9744, 'lng': 14.4742, 'name': 'České Budějovice centrum'}
            ])),
            # Liberec - Hradec Králové
            (4, 'Liberec', 'Hradec Králové', tomorrow, 1, 200, json.dumps([
                {'lat': 50.7663, 'lng': 15.0543, 'name': 'Liberec centrum'},
                {'lat': 50.2103, 'lng': 15.8327, 'name': 'Hradec Králové centrum'}
            ])),
            # Olomouc - Zlín
            (5, 'Olomouc', 'Zlín', tomorrow, 2, 150, json.dumps([
                {'lat': 49.5938, 'lng': 17.2509, 'name': 'Olomouc centrum'},
                {'lat': 49.2238, 'lng': 17.6696, 'name': 'Zlín centrum'}
            ]))
        ]
        
        for ride in rides:
            c.execute('''INSERT INTO rides 
                         (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', ride)
        
        conn.commit()
        conn.close()
        print("Testovaci data pridana!")
        print("Pridano 5 uzivatelu a 5 jizd s GPS souradnicemi")
        print("Vsichni uzivatele maji heslo: heslo123")

    except Exception as e:
        print("An error occurred:")
        traceback.print_exc()

if __name__ == '__main__':
    add_test_data()