import sqlite3

DATABASE = 'spolujizda.db'

def fix_database():
    print("=== OPRAVA DATABÁZE ===")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # 1. Smaž jízdy s neexistujícími řidiči (user_id NULL nebo neexistuje)
    print("1. Mazání jízd s neexistujícími řidiči...")
    c.execute('''DELETE FROM rides WHERE user_id IS NULL 
                 OR user_id NOT IN (SELECT id FROM users)''')
    deleted_rides = c.rowcount
    print(f"   Smazáno {deleted_rides} jízd s neexistujícími řidiči")
    
    # 2. Smaž testovací uživatele
    print("2. Mazání testovacích uživatelů...")
    test_patterns = ['test', 'testovací', 'robot']
    deleted_users = 0
    
    for pattern in test_patterns:
        c.execute('SELECT id, name FROM users WHERE LOWER(name) LIKE ?', (f'%{pattern}%',))
        users = c.fetchall()
        
        for user in users:
            user_id, name = user
            print(f"   Mazání uživatele {user_id}: '{name}'")
            
            # Smaž všechny související záznamy
            c.execute('DELETE FROM rides WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM reservations WHERE passenger_id = ?', (user_id,))
            c.execute('DELETE FROM messages WHERE sender_id = ?', (user_id,))
            c.execute('DELETE FROM ratings WHERE rater_id = ? OR rated_id = ?', (user_id, user_id))
            # c.execute('DELETE FROM user_locations WHERE user_id = ?', (user_id,))  # Tabulka neexistuje
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
            deleted_users += 1
    
    print(f"   Smazáno {deleted_users} testovacích uživatelů")
    
    conn.commit()
    conn.close()
    
    print("=== OPRAVA DOKONČENA ===")

if __name__ == "__main__":
    fix_database()