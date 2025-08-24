import sqlite3
from datetime import datetime, timedelta
import random

DATABASE = 'spolujizda.db'

def add_test_rides():
    print("=== PŘIDÁVÁNÍ TESTOVACÍCH JÍZD ===")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Získej ID uživatelů
    c.execute('SELECT id FROM users')
    user_ids = [row[0] for row in c.fetchall()]
    
    if not user_ids:
        print("Žádní uživatelé v databázi!")
        return
    
    # Testovací jízdy s reálnými údaji
    test_rides = [
        ('Praha', 'Brno', '2024-01-15 08:00:00', 3, 250),
        ('Brno', 'Praha', '2024-01-15 18:30:00', 2, 280),
        ('Praha', 'Ostrava', '2024-01-16 07:15:00', 4, 320),
        ('Ostrava', 'Praha', '2024-01-16 16:45:00', 1, 350),
        ('Brno', 'Ostrava', '2024-01-17 09:30:00', 3, 200),
        ('Plzeň', 'Praha', '2024-01-17 14:20:00', 2, 150),
        ('Praha', 'České Budějovice', '2024-01-18 10:00:00', 3, 180),
        ('Liberec', 'Praha', '2024-01-18 15:30:00', 2, 120),
        ('Praha', 'Hradec Králové', '2024-01-19 08:45:00', 4, 160),
        ('Olomouc', 'Brno', '2024-01-19 17:00:00', 1, 100),
        ('Brno', 'Zlín', '2024-01-20 11:15:00', 3, 80),
        ('Pardubice', 'Praha', '2024-01-20 13:30:00', 2, 140),
        ('Praha', 'Karlovy Vary', '2024-01-21 09:00:00', 3, 200),
        ('Jihlava', 'Brno', '2024-01-21 16:15:00', 2, 90),
        ('Praha', 'Teplice', '2024-01-22 07:30:00', 4, 170)
    ]
    
    added_count = 0
    for ride in test_rides:
        from_loc, to_loc, departure, seats, price = ride
        user_id = random.choice(user_ids)
        
        try:
            c.execute('''INSERT INTO rides 
                         (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, from_loc, to_loc, departure, seats, price, '[]'))
            added_count += 1
            print(f"  Přidána jízda: {from_loc} -> {to_loc} ({price} Kc)")
        except Exception as e:
            print(f"  Chyba při přidávání jízdy {from_loc} -> {to_loc}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Přidáno {added_count} testovacích jízd")
    print("=== DOKONČENO ===")

if __name__ == "__main__":
    add_test_rides()