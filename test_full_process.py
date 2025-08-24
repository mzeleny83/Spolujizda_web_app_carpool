import sqlite3
import hashlib
import json

DATABASE = 'spolujizda.db'

def test_registration_and_login():
    print("=== TEST REGISTRACE A PŘIHLÁŠENÍ ===")
    
    # Test data
    name = "Kamarádka Test"
    phone = "+420777888999"
    email = "kamaradka@test.cz"
    password = "mojeHeslo123"
    
    # 1. REGISTRACE
    print(f"\n1. Registrace uživatele: {name}")
    
    # Normalizace telefonu
    phone_clean = ''.join(filter(str.isdigit, phone))
    if phone_clean.startswith('420'):
        phone_clean = phone_clean[3:]
    phone_full = f'+420{phone_clean}'
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Zkontroluj existující telefon
        c.execute('SELECT id FROM users WHERE phone = ?', (phone_full,))
        if c.fetchone():
            print("POZOR Telefon uz je registrovan, mazu stary zaznam...")
            c.execute('DELETE FROM users WHERE phone = ?', (phone_full,))
        
        # Registruj
        c.execute('INSERT INTO users (name, phone, email, password_hash, rating) VALUES (?, ?, ?, ?, ?)',
                 (name, phone_full, email, password_hash, 5.0))
        conn.commit()
        user_id = c.lastrowid
        print(f"OK Registrace uspesna! User ID: {user_id}")
        
        conn.close()
        
    except Exception as e:
        print(f"CHYBA registrace: {e}")
        return
    
    # 2. PŘIHLÁŠENÍ
    print(f"\n2. Přihlášení s heslem: {password}")
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Zkus přihlášení telefonem
        c.execute('SELECT id, name, rating FROM users WHERE phone = ? AND password_hash = ?',
                 (phone_full, password_hash))
        user = c.fetchone()
        
        if user:
            print(f"OK Prihlaseni uspesne!")
            print(f"   User ID: {user[0]}")
            print(f"   Jméno: {user[1]}")
            print(f"   Rating: {user[2]}")
        else:
            print("CHYBA Prihlaseni neuspesne - neplatne udaje")
        
        # Zkus také přihlášení emailem
        print(f"\n3. Přihlášení emailem: {email}")
        c.execute('SELECT id, name, rating FROM users WHERE email = ? AND password_hash = ?',
                 (email, password_hash))
        user_email = c.fetchone()
        
        if user_email:
            print("OK Prihlaseni emailem take funguje!")
        else:
            print("CHYBA Prihlaseni emailem nefunguje")
        
        conn.close()
        
    except Exception as e:
        print(f"CHYBA prihlaseni: {e}")

def test_existing_users():
    print("\n=== TEST EXISTUJÍCÍCH UŽIVATELŮ ===")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT name, phone, password_hash FROM users LIMIT 3')
    users = c.fetchall()
    
    for user in users:
        print(f"Uživatel: {user[0]}, Telefon: {user[1]}")
        
        # Test přihlášení s heslem "heslo123"
        test_hash = hashlib.sha256("heslo123".encode()).hexdigest()
        if user[2] == test_hash:
            print("  OK Heslo je 'heslo123'")
        else:
            print("  CHYBA Heslo neni 'heslo123'")
    
    conn.close()

if __name__ == "__main__":
    test_existing_users()
    test_registration_and_login()