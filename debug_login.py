import sqlite3
import hashlib

def test_login():
    phone = "+420123456789"
    password = "test123"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    print(f"Zkouším přihlášení: {phone}")
    print(f"Zadané heslo: {password}")
    print(f"Hash zadaného hesla: {password_hash}")
    
    conn = sqlite3.connect('spolujizda.db')
    c = conn.cursor()
    
    # Najdi uživatele podle telefonu
    c.execute('SELECT id, name, password_hash FROM users WHERE phone = ?', (phone,))
    user = c.fetchone()
    
    if user:
        print(f"Uživatel nalezen: ID={user[0]}, Jméno={user[1]}")
        print(f"Hash v databázi: {user[2]}")
        print(f"Hashe se shodují: {user[2] == password_hash}")
        
        # Zkus přihlášení
        c.execute('SELECT id, name, rating FROM users WHERE phone = ? AND password_hash = ?',
                 (phone, password_hash))
        login_result = c.fetchone()
        
        if login_result:
            print(f"✅ Přihlášení úspěšné: {login_result}")
        else:
            print("❌ Přihlášení neúspěšné - neplatné údaje")
    else:
        print("❌ Uživatel nenalezen")
    
    conn.close()

def test_all_users():
    print("\n=== Všichni uživatelé ===")
    conn = sqlite3.connect('spolujizda.db')
    c = conn.cursor()
    c.execute('SELECT id, name, phone, password_hash FROM users LIMIT 5')
    users = c.fetchall()
    
    for user in users:
        print(f"ID: {user[0]}, Jméno: {user[1]}, Telefon: {user[2]}, Hash: {user[3][:20]}...")
    
    conn.close()

if __name__ == "__main__":
    test_all_users()
    test_login()