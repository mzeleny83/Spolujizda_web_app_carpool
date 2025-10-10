import os
import sqlite3
import random
import datetime

def populate_dummy_data():
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///spolujizda.db')

    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
    else:
        # For PostgreSQL, you'd use psycopg2
        # import psycopg2
        # conn = psycopg2.connect(db_url)
        print("Warning: This script is primarily designed for SQLite. For PostgreSQL, you'll need to install psycopg2 and uncomment the relevant lines.")
        return

    cursor = conn.cursor()

    try:
        # 1. Update home_city for existing users
        cities = ['Praha', 'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Olomouc', 'Zlín', 'České Budějovice', 'Hradec Králové', 'Pardubice']
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]

        for user_id in user_ids:
            home_city = random.choice(cities)
            cursor.execute("UPDATE users SET home_city = ? WHERE id = ?", (home_city, user_id))
        print(f"Updated home_city for {len(user_ids)} users.")

        # 2. Add dummy rides
        if not user_ids:
            print("No users found to create rides. Please register some users first.")
            return

        for _ in range(20): # Add 20 dummy rides
            user_id = random.choice(user_ids)
            from_location = random.choice(cities)
            to_location = random.choice(cities)
            while to_location == from_location:
                to_location = random.choice(cities)
            
            departure_time = datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 30), hours=random.randint(0, 23), minutes=random.choice([0, 15, 30, 45]))
            available_seats = random.randint(1, 4)
            price_per_person = random.randint(50, 300)
            route_waypoints = json.dumps([]) # Empty for dummy data

            cursor.execute("INSERT INTO rides (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints))
        print("Added 20 dummy rides.")

        # 3. Add dummy reservations
        cursor.execute("SELECT id, user_id, available_seats FROM rides")
        rides_data = cursor.fetchall()

        if not rides_data:
            print("No rides found to create reservations.")
            return

        for _ in range(30): # Add 30 dummy reservations
            ride_id, driver_id, available_seats = random.choice(rides_data)
            if available_seats <= 0: # Skip if no seats left
                continue

            passenger_id = random.choice(user_ids)
            while passenger_id == driver_id: # Passenger cannot be the driver of the same ride
                passenger_id = random.choice(user_ids)
            
            seats_reserved = random.randint(1, min(available_seats, 2)) # Reserve 1 or 2 seats
            status = 'confirmed'

            cursor.execute("INSERT INTO reservations (ride_id, passenger_id, seats_reserved, status) VALUES (?, ?, ?, ?)",
                           (ride_id, passenger_id, seats_reserved, status))
            # Update available seats in rides table
            cursor.execute("UPDATE rides SET available_seats = available_seats - ? WHERE id = ?", (seats_reserved, ride_id))
        print("Added 30 dummy reservations.")

        conn.commit()
        print("Dummy data population complete.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    populate_dummy_data()