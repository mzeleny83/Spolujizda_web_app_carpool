import sqlite3
import hashlib
from datetime import datetime, timedelta

DATABASE = 'spolujizda.db'

def add_sample_data():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Přidá testovací uživatele
    users = [
        ('Jan Novák', '+420123456789', 'jan@email.cz', 'heslo123'),
        ('Marie Svobodová', '+420987654321', 'marie@email.cz', 'heslo456'),
        ('Petr Dvořák', '+420555666777', 'petr@email.cz', 'heslo789')
    ]
    
    for name, phone, email, password in users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            c.execute('INSERT INTO users (name, phone, email, password_hash, rating) VALUES (?, ?, ?, ?, ?)',
                     (name, phone, email, password_hash, 5.0))
        except sqlite3.IntegrityError:
            pass  # Uživatel už existuje
    
    # Přidá testovací jízdy
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
    day_after = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M')
    
    rides = [
        (1, 'Praha', 'Brno', tomorrow, 3, 200, '[]'),
        (2, 'Brno', 'Ostrava', day_after, 2, 150, '[]'),
        (1, 'Praha', 'Plzeň', tomorrow, 4, 100, '[]'),
        (3, 'Ostrava', 'Praha', day_after, 1, 250, '[]'),
        (2, 'Brno', 'Praha', tomorrow, 2, 180, '[]')
    ]
    
    for user_id, from_loc, to_loc, dep_time, seats, price, waypoints in rides:
        try:
            c.execute('''INSERT INTO rides 
                         (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (user_id, from_loc, to_loc, dep_time, seats, price, waypoints))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print("Testovací data přidána!")

if __name__ == '__main__':
    add_sample_data()