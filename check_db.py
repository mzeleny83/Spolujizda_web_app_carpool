import sqlite3

try:
    conn = sqlite3.connect('spolujizda.db')
    c = conn.cursor()
    
    # Zkontroluj jestli tabulka existuje
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = c.fetchone()
    print(f"Tabulka users existuje: {table_exists is not None}")
    
    if table_exists:
        # Zobraz všechny uživatele
        c.execute('SELECT id, name, phone, password_hash FROM users')
        users = c.fetchall()
        print(f"Počet uživatelů: {len(users)}")
        
        for user in users:
            print(f"ID: {user[0]}, Jméno: {user[1]}, Telefon: {user[2]}, Hash: {user[3][:20]}...")
    
    conn.close()
    
except Exception as e:
    print(f"Chyba: {e}")