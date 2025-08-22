import sqlite3

DATABASE = 'spolujizda.db'

def check_db():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        print("--- Rides ---")
        for row in c.execute("SELECT * FROM rides"):
            print(row)
        print("--- Users ---")
        for row in c.execute("SELECT * FROM users"):
            print(row)
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_db()