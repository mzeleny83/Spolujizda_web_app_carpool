import sqlite3

# Připoj se k databázi
conn = sqlite3.connect('spolujizda.db')
c = conn.cursor()

print("=== DEBUG VYHLEDÁVÁNÍ UŽIVATELŮ ===\n")

# 1. Zkontroluj všechny uživatele
print("1. Všichni uživatelé v databázi:")
c.execute('SELECT name, home_city FROM users')
users = c.fetchall()
for user in users:
    print(f"   - {user[0]}: {user[1] or 'NULL'}")

# 2. Zkontroluj konkrétně Miroslava Zeleného
print("\n2. Miroslav Zelený:")
c.execute('SELECT name, home_city FROM users WHERE name = ?', ('Miroslav Zelený',))
miroslav = c.fetchone()
if miroslav:
    print(f"   - Jméno: '{miroslav[0]}'")
    print(f"   - Město: '{miroslav[1]}'")
else:
    print("   - NENALEZEN!")

# 3. Zkontroluj vyhledávání podle jména
print("\n3. Vyhledávání podle jména 'Miroslav':")
c.execute('SELECT name, home_city FROM users WHERE name LIKE ?', ('%Miroslav%',))
results = c.fetchall()
for result in results:
    print(f"   - {result[0]}: {result[1]}")

# 4. Zkontroluj vyhledávání podle města
print("\n4. Vyhledávání podle města 'Brno':")
c.execute('SELECT name, home_city FROM users WHERE home_city = ?', ('Brno',))
results = c.fetchall()
for result in results:
    print(f"   - {result[0]}: {result[1]}")

# 5. Zkontroluj kombinované vyhledávání
print("\n5. Kombinované vyhledávání (jméno LIKE '%Miroslav%' AND město = 'Brno'):")
c.execute('SELECT name, home_city FROM users WHERE name LIKE ? AND home_city = ?', ('%Miroslav%', 'Brno'))
results = c.fetchall()
for result in results:
    print(f"   - {result[0]}: {result[1]}")

# 6. Simuluj API dotaz
print("\n6. Simulace API dotazu /api/users/search?q=Miroslav&city=Brno:")
query = 'Miroslav'
city_filter = 'Brno'

sql = '''
    SELECT u.id, u.name, u.rating, u.total_rides, u.verified, u.created_at, u.home_city
    FROM users u
    WHERE u.name LIKE ?
'''
params = [f'%{query}%']

if city_filter:
    sql += ' AND u.home_city = ?'
    params.append(city_filter)

c.execute(sql, params)
results = c.fetchall()

print(f"   SQL: {sql}")
print(f"   Parametry: {params}")
print(f"   Výsledky: {len(results)}")
for result in results:
    print(f"   - {result[1]}: {result[6]}")

conn.close()
print("\n=== KONEC DEBUG ===")