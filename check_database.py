import sqlite3

DATABASE = 'spolujizda.db'

def check_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    print("=== KONTROLA DATABÁZE ===")
    
    # Zobraz všechny uživatele
    c.execute('SELECT id, name FROM users')
    users = c.fetchall()
    
    print(f"Celkem uživatelů: {len(users)}")
    for user in users:
        print(f"  ID {user[0]}: '{user[1]}'")
    
    # Zobraz všechny jízdy s řidiči
    c.execute('SELECT r.id, r.from_location, r.to_location, u.name FROM rides r LEFT JOIN users u ON r.user_id = u.id')
    rides = c.fetchall()
    
    print(f"\nCelkem jízd: {len(rides)}")
    for ride in rides:
        print(f"  Jízda {ride[0]}: {ride[1]} -> {ride[2]}, řidič: '{ride[3]}'")
    
    conn.close()

if __name__ == "__main__":
    check_database()