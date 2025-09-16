import sqlite3

db_file = 'spolujizda.db'

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Add the created_at column
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
        print("Column 'created_at' added to 'users' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'created_at' already exists.")
        else:
            raise

    # Set a default value for existing users
    cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    print(f"{cursor.rowcount} rows updated.")

    conn.commit()
    conn.close()
    print("Database updated successfully.")

except Exception as e:
    print(f"An error occurred: {e}")
