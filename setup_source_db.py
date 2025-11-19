import sqlite3
import json
import hashlib
from datetime import datetime, timedelta

DATABASE = 'spolujizda.db'

def setup_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(120),
        phone VARCHAR(20) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        rating FLOAT,
        created_at DATETIME,
        UNIQUE (email),
        UNIQUE (phone)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS rides (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        from_location VARCHAR(200) NOT NULL,
        to_location VARCHAR(200) NOT NULL,
        departure_time DATETIME NOT NULL,
        available_seats INTEGER NOT NULL,
        price_per_person FLOAT,
        route_waypoints TEXT,
        created_at DATETIME
    )
    """)

    # Add test users
    users = [
        ('Jan Novák', '+420123456789', 'jan@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.8),
        ('Marie Svobodová', '+420987654321', 'marie@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.9),
        ('Petr Dvořák', '+420555666777', 'petr@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.7),
        ('Anna Nováková', '+420111222333', 'anna@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 5.0),
        ('Tomáš Procházka', '+420444555666', 'tomas@email.cz', hashlib.sha256('heslo123'.encode()).hexdigest(), 4.6)
    ]

    try:
        for user in users:
            c.execute('INSERT INTO users (name, phone, email, password_hash, rating) VALUES (?, ?, ?, ?, ?)', user)
    except sqlite3.IntegrityError:
        print("Users already exist.")


    # Add test rides
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')

    rides = [
        (1, 'Praha', 'Brno', tomorrow, 3, 300, json.dumps([
            {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'},
            {'lat': 49.1951, 'lng': 16.6068, 'name': 'Brno centrum'}
        ])),
        (2, 'Ostrava', 'Praha', tomorrow, 2, 400, json.dumps([
            {'lat': 49.8209, 'lng': 18.2625, 'name': 'Ostrava centrum'},
            {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'}
        ])),
        (3, 'Plzeň', 'České Budějovice', tomorrow, 4, 250, json.dumps([
            {'lat': 49.7384, 'lng': 13.3736, 'name': 'Plzeň centrum'},
            {'lat': 48.9744, 'lng': 14.4742, 'name': 'České Budějovice centrum'}
        ])),
        (4, 'Liberec', 'Hradec Králové', tomorrow, 1, 200, json.dumps([
            {'lat': 50.7663, 'lng': 15.0543, 'name': 'Liberec centrum'},
            {'lat': 50.2103, 'lng': 15.8327, 'name': 'Hradec Králové centrum'}
        ])),
        (5, 'Olomouc', 'Zlín', tomorrow, 2, 150, json.dumps([
            {'lat': 49.5938, 'lng': 17.2509, 'name': 'Olomouc centrum'},
            {'lat': 49.2238, 'lng': 17.6696, 'name': 'Zlín centrum'}
        ]))
    ]
    
    try:
        for ride in rides:
            c.execute('''INSERT INTO rides
                         (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', ride)
    except sqlite3.IntegrityError:
        print("Rides already exist.")


    conn.commit()
    conn.close()
    print("Database 'spolujizda.db' created and populated with test data.")

if __name__ == '__main__':
    setup_database()
