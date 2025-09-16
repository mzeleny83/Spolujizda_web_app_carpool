import os
import psycopg2
import sys

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("DATABASE_URL environment variable not set.")
    sys.exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    # Add the created_at column
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP")
        print("Column 'created_at' added to 'users' table.")
    except psycopg2.errors.DuplicateColumn:
        print("Column 'created_at' already exists.")
        conn.rollback()
    except Exception as e:
        print(f"Error adding column: {e}")
        conn.rollback()
        raise

    # Set a default value for existing users
    cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    print(f"{cursor.rowcount} rows updated.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database updated successfully.")

except Exception as e:
    print(f"An error occurred: {e}")