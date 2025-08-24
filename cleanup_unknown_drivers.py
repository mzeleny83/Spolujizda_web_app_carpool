import sqlite3

DATABASE = 'spolujizda.db'

def cleanup_unknown_drivers():
    print("=== MAZÁNÍ NEZNÁMÝCH ŘIDIČŮ ===")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Smaž uživatele s jménem "Neznámý řidič" nebo podobnými
    unknown_patterns = ['neznámý řidič', 'neznámý', 'unknown', 'driver', 'řidič', 'neznamy ridic']
    
    deleted_users = 0
    for pattern in unknown_patterns:
        c.execute('SELECT id, name FROM users WHERE LOWER(name) LIKE ?', (f'%{pattern}%',))
        users = c.fetchall()
        
        for user in users:
            user_id, name = user
            print(f"  Mazání uživatele {user_id}: '{name}'")
            
            # Smaž všechny související záznamy
            c.execute('DELETE FROM rides WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM reservations WHERE passenger_id = ?', (user_id,))
            c.execute('DELETE FROM messages WHERE sender_id = ?', (user_id,))
            c.execute('DELETE FROM ratings WHERE rater_id = ? OR rated_id = ?', (user_id, user_id))
            c.execute('DELETE FROM user_locations WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
            deleted_users += 1
    
    print(f"Smazáno {deleted_users} neznámých řidičů")
    
    conn.commit()
    conn.close()
    
    print("=== ČIŠTĚNÍ DOKONČENO ===")

if __name__ == "__main__":
    cleanup_unknown_drivers()