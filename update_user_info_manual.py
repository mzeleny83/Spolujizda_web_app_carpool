import os
import sqlite3
import json
import datetime
import requests

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///spolujizda.db')
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        return sqlite3.connect(db_path)
    else:
        print("Error: This script currently only supports SQLite. Please configure DATABASE_URL to use SQLite or extend the script for PostgreSQL.")
        return None

def get_user_ids():
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def update_user_profile_api(user_id, data):
    # Assuming the Flask app is running locally on port 5000
    # In a real scenario, you might need to configure the base URL
    base_url = os.environ.get('FLASK_APP_BASE_URL', 'http://localhost:5000')
    url = f"{base_url}/api/users/{user_id}/profile"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        print(f"API response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error updating profile via API: {e}")
        return False

def add_ride_to_db(user_id, from_location, to_location, departure_time_str, available_seats, price_per_person):
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        departure_time = datetime.datetime.strptime(departure_time_str, "%Y-%m-%d %H:%M")
        cursor.execute("INSERT INTO rides (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (user_id, from_location, to_location, departure_time, available_seats, price_per_person, json.dumps([])))
        conn.commit()
        print(f"Added ride for user {user_id}: {from_location} to {to_location}")
        return True
    except sqlite3.Error as e:
        print(f"Database error adding ride: {e}")
        return False
    finally:
        conn.close()

def add_reservation_to_db(passenger_id, ride_id, seats_reserved):
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO reservations (ride_id, passenger_id, seats_reserved, status) VALUES (?, ?, ?, ?)",
                       (ride_id, passenger_id, seats_reserved, 'confirmed'))
        # Update available seats in rides table
        cursor.execute("UPDATE rides SET available_seats = available_seats - ? WHERE id = ?", (seats_reserved, ride_id))
        conn.commit()
        print(f"Added reservation for passenger {passenger_id} on ride {ride_id}")
        return True
    except sqlite3.Error as e:
        print(f"Database error adding reservation: {e}")
        return False
    finally:
        conn.close()

def main():
    print("\n--- Update User Information Manually ---")
    users = get_user_ids()
    if not users:
        print("No users found in the database. Please register some users first.")
        return

    print("Registered Users:")
    for user_id, name in users:
        print(f"  ID: {user_id}, Name: {name}")

    while True:
        try:
            user_id_input = input("\nEnter User ID to update (or 'q' to quit): ")
            if user_id_input.lower() == 'q':
                break
            user_id = int(user_id_input)
            if user_id not in [u[0] for u in users]:
                print("Invalid User ID. Please choose from the list above.")
                continue

            print(f"\nUpdating information for User ID: {user_id}")

            # Update home_city
            home_city = input(f"Enter new Home City (current: {get_user_profile_api(user_id).get('home_city', 'N/A')}, leave blank to skip): ")
            if home_city:
                update_user_profile_api(user_id, {'home_city': home_city})

            # Add a ride as driver
            add_ride = input("Add a ride as driver for this user? (y/n): ").lower()
            if add_ride == 'y':
                from_loc = input("  From Location: ")
                to_loc = input("  To Location: ")
                dep_time = input("  Departure Time (YYYY-MM-DD HH:MM): ")
                seats = int(input("  Available Seats: "))
                price = int(input("  Price Per Person: "))
                add_ride_to_db(user_id, from_loc, to_loc, dep_time, seats, price)

            # Add a reservation as passenger
            add_reservation = input("Add a reservation as passenger for this user? (y/n): ").lower()
            if add_reservation == 'y':
                conn = get_db_connection()
                if not conn: continue
                cursor = conn.cursor()
                cursor.execute("SELECT id, from_location, to_location, departure_time FROM rides")
                rides = cursor.fetchall()
                conn.close()

                if not rides:
                    print("No rides available to make a reservation.")
                else:
                    print("Available Rides:")
                    for ride_id, from_loc, to_loc, dep_time in rides:
                        print(f"  ID: {ride_id}, From: {from_loc}, To: {to_loc}, Time: {dep_time}")
                    
                    ride_id_res = int(input("  Enter Ride ID to reserve: "))
                    seats_res = int(input("  Seats to reserve: "))
                    add_reservation_to_db(user_id, ride_id_res, seats_res)

        except ValueError:
            print("Invalid input. Please enter a number for User ID, seats, or price.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    print("Exiting manual user update script.")

if __name__ == '__main__':
    main()
