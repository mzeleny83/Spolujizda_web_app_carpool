import sqlite3

DATABASE = 'spolujizda.db'

def cleanup_database():
    print("=== ČIŠTĚNÍ DATABÁZE ===")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Seznam platných českých měst
    valid_cities = [
        'Praha', 'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Olomouc', 'Zlín', 
        'České Budějovice', 'Hradec Králové', 'Pardubice', 'Havířov', 
        'Kladno', 'Most', 'Opava', 'Frýdek-Místek', 'Karviná', 'Jihlava', 
        'Teplice', 'Děčín', 'Karlovy Vary', 'Jablonec nad Nisou', 'Mladá Boleslav',
        'Prostějov', 'Přerov', 'Česká Lípa', 'Uherské Hradiště', 'Třebíč',
        'Rájec Jestřebí'
    ]
    
    # 1. Smaž jízdy s neplatnými městy
    print("1. Mazání jízd s neplatnými městy...")
    
    c.execute('SELECT id, from_location, to_location FROM rides')
    rides = c.fetchall()
    
    deleted_rides = 0
    for ride in rides:
        ride_id, from_loc, to_loc = ride
        
        # Extrahuj město z lokace (před první čárkou)
        from_city = from_loc.split(',')[0].strip() if from_loc else ''
        to_city = to_loc.split(',')[0].strip() if to_loc else ''
        
        if from_city not in valid_cities or to_city not in valid_cities:
            print(f"  Mazání jízdy {ride_id}: {from_loc} -> {to_loc}")
            c.execute('DELETE FROM rides WHERE id = ?', (ride_id,))
            deleted_rides += 1
    
    print(f"  Smazáno {deleted_rides} jízd s neplatnými městy")
    
    # 2. Smaž anonymní uživatele (bez jména nebo s generickými jmény)
    print("2. Mazání anonymních uživatelů...")
    
    c.execute('SELECT id, name FROM users')
    users = c.fetchall()
    
    deleted_users = 0
    anonymous_patterns = ['test', 'user', 'anonym', 'guest', 'admin', 'null', 'undefined', '']
    
    for user in users:
        user_id, name = user
        
        if not name or name.lower().strip() in anonymous_patterns or len(name.strip()) < 2:
            print(f"  Mazání uživatele {user_id}: '{name}'")
            # Smaž všechny související záznamy
            c.execute('DELETE FROM rides WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM reservations WHERE passenger_id = ?', (user_id,))
            c.execute('DELETE FROM messages WHERE sender_id = ?', (user_id,))
            c.execute('DELETE FROM ratings WHERE rater_id = ? OR rated_id = ?', (user_id, user_id))
            c.execute('DELETE FROM user_locations WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
            deleted_users += 1
    
    print(f"  Smazáno {deleted_users} anonymních uživatelů")
    
    conn.commit()
    conn.close()
    
    print("=== ČIŠTĚNÍ DOKONČENO ===")

if __name__ == "__main__":
    cleanup_database()