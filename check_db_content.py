import sqlite3
import os

db_path = 'spolujizda.db'
# Get the absolute path to the database file
script_dir = os.path.dirname(os.path.abspath(__file__))
absolute_db_path = os.path.join(script_dir, db_path)

print(f"Attempting to connect to database at: {absolute_db_path}")

try:
    conn = sqlite3.connect(absolute_db_path)
    c = conn.cursor()

    print("\n--- Tables in the database ---")
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    for table in tables:
        print(table[0])

    print("\n--- Schema for 'rides' table ---")
    c.execute("PRAGMA table_info(rides);")
    schema = c.fetchall()
    for col in schema:
        print(col)

    print("\n--- First 5 rows from 'rides' table ---")
    c.execute("SELECT * FROM rides LIMIT 5;")
    rides = c.fetchall()
    if rides:
        for ride in rides:
            print(ride)
    else:
        print("No rides found in the 'rides' table.")

    conn.close()

except sqlite3.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
