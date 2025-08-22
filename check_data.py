import sqlite3

conn = sqlite3.connect('spolujizda.db')
c = conn.cursor()

print("=== UŽIVATELÉ ===")
c.execute('SELECT * FROM users')
users = c.fetchall()
for user in users:
    print(f"ID: {user[0]}, Jméno: {user[1]}, Telefon: {user[2]}")

print("\n=== JÍZDY ===")
c.execute('SELECT * FROM rides')
rides = c.fetchall()
for ride in rides:
    print(f"ID: {ride[0]}, Od: {ride[2]}, Do: {ride[3]}, Čas: {ride[4]}")

print(f"\nCelkem uživatelů: {len(users)}")
print(f"Celkem jízd: {len(rides)}")

conn.close()