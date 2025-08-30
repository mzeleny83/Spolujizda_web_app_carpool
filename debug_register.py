import sqlite3
import hashlib

# Zkus registraci přímo v databázi
def test_register():
    # Nejdříve vytvoř tabulky
    conn = sqlite3.connect('spolujizda.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              phone TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              rating REAL DEFAULT 5.0,
              total_rides INTEGER DEFAULT 0,
              verified BOOLEAN DEFAULT 0,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    
    name = "Test User"
    phone = "+420123456789"
    password = "test123"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    print(f"Registruji: {name}, {phone}, hash: {password_hash[:20]}...")
    
    try:
        conn = sqlite3.connect('spolujizda.db')
        c = conn.cursor()
        
        # Zkontroluj existující
        c.execute('SELECT id FROM users WHERE phone = ?', (phone,))
        existing = c.fetchone()
        if existing:
            print(f"Uživatel už existuje: {existing[0]}")
            conn.close()
            return
        
        # Registruj
        c.execute('INSERT INTO users (name, phone, password_hash, rating) VALUES (?, ?, ?, ?)',
                 (name, phone, password_hash, 5.0))
        conn.commit()
        user_id = c.lastrowid
        print(f"Uživatel registrován s ID: {user_id}")
        
        # Ověř
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        print(f"Ověření: {user}")
        
        conn.close()
        
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    test_register()