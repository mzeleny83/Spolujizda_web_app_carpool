import sqlite3

# Zkontroluj co je v databázi
conn = sqlite3.connect('spolujizda.db')
c = conn.cursor()

print("=== UŽIVATELÉ ===")
c.execute('SELECT id, name, phone FROM users')
users = c.fetchall()
for user in users:
    print(f"ID: {user[0]}, Jméno: {user[1]}, Telefon: {user[2]}")

print("\n=== JÍZDY ===")
c.execute('SELECT id, user_id, from_location, to_location, available_seats, price_per_person FROM rides')
rides = c.fetchall()
for ride in rides:
    print(f"ID: {ride[0]}, User: {ride[1]}, {ride[2]} -> {ride[3]}, Místa: {ride[4]}, Cena: {ride[5]}")

print(f"\nCelkem uživatelů: {len(users)}")
print(f"Celkem jízd: {len(rides)}")

conn.close()