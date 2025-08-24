#!/usr/bin/env python3
import sqlite3
import random
import hashlib
from datetime import datetime, timedelta

DATABASE = 'spolujizda.db'

# Náhodná jména
names = [
    "Jan Novák", "Petr Svoboda", "Pavel Novotný", "Jana Svobodová", "Eva Nováková",
    "Tomáš Dvořák", "Marie Černá", "Jiří Procházka", "Anna Krejčí", "Martin Pospíšil",
    "Lenka Veselá", "David Horák", "Tereza Marešová", "Lukáš Pokorný", "Barbora Růžičková"
]

# Města z databáze
cities = [
    "Praha", "Brno", "Ostrava", "Plzeň", "Liberec", 
    "Olomouc", "České Budějovice", "Hradec Králové", "Pardubice", "Zlín"
]

def create_test_data():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Zjisti kolik už je uživatelů
    c.execute('SELECT COUNT(*) FROM users')
    current_users = c.fetchone()[0]
    
    users_to_create = max(0, 10 - current_users)
    
    print(f"Aktuálně v databázi: {current_users} uživatelů")
    print(f"Vytvářím {users_to_create} nových uživatelů...")
    
    created_user_ids = []
    
    # Vytvoř uživatele
    for i in range(users_to_create):
        name = random.choice(names)
        phone = f"+420{random.randint(600000000, 799999999)}"
        city = random.choice(cities)
        password_hash = hashlib.sha256("test123".encode()).hexdigest()
        
        try:
            c.execute('''INSERT INTO users (name, phone, password_hash, home_city, rating) 
                         VALUES (?, ?, ?, ?, ?)''',
                     (name, phone, password_hash, city, round(random.uniform(3.5, 5.0), 1)))
            created_user_ids.append(c.lastrowid)
        except sqlite3.IntegrityError:
            # Telefon už existuje, zkus jiný
            phone = f"+420{random.randint(600000000, 799999999)}"
            c.execute('''INSERT INTO users (name, phone, password_hash, home_city, rating) 
                         VALUES (?, ?, ?, ?, ?)''',
                     (name, phone, password_hash, city, round(random.uniform(3.5, 5.0), 1)))
            created_user_ids.append(c.lastrowid)
    
    # Vytvoř jízdy pro nové uživatele
    print(f"Vytvářím jízdy...")
    
    for user_id in created_user_ids:
        # Každý uživatel nabídne 1-2 jízdy
        num_rides = random.randint(1, 2)
        
        for _ in range(num_rides):
            from_city = random.choice(cities)
            to_city = random.choice([c for c in cities if c != from_city])
            
            # Náhodný čas v příštích 7 dnech
            future_date = datetime.now() + timedelta(days=random.randint(0, 7))
            departure_time = future_date.strftime("%Y-%m-%dT%H:%M")
            
            price = random.randint(50, 500)  # 50-500 Kč
            seats = random.randint(1, 4)
            
            c.execute('''INSERT INTO rides (user_id, from_location, to_location, departure_time, 
                                          available_seats, price_per_person, route_waypoints)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (user_id, from_city, to_city, departure_time, seats, price, "[]"))
    
    conn.commit()
    
    # Zjisti celkový počet
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM rides')
    total_rides = c.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Hotovo!")
    print(f"   Celkem uživatelů: {total_users}")
    print(f"   Celkem jízd: {total_rides}")
    print(f"   Heslo pro všechny testovací uživatele: test123")

if __name__ == "__main__":
    create_test_data()