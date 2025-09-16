import sqlite3

db_file = 'spolujizda.db'

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"Number of users: {count}")

    cursor.execute("SELECT id, name, created_at FROM users")
    rows = cursor.fetchall()

    for row in rows:
        print(f"User ID: {row[0]}, Name: {row[1]}, Created At: {row[2]}")

    conn.close()

except Exception as e:
    print(f"An error occurred: {e}")