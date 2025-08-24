import sqlite3

# Připoj se k databázi
conn = sqlite3.connect('spolujizda.db')
c = conn.cursor()

# Zkontroluj existující uživatele
print("Existující uživatelé:")
c.execute('SELECT name, home_city FROM users')
users = c.fetchall()
for user in users:
    print(f"- {user[0]}: {user[1] or 'Bez města'}")

# Najdi Miroslava Zeleného
c.execute('SELECT name FROM users WHERE name LIKE "%Miroslav%" OR name LIKE "%Zelený%"')
miroslav = c.fetchall()

if miroslav:
    user_name = miroslav[0][0]
    print(f"\nNalezen uživatel: {user_name}")
    
    # Aktualizuj město na Brno
    c.execute('UPDATE users SET home_city = ? WHERE name = ?', ('Brno', user_name))
    conn.commit()
    
    print(f"Město aktualizováno na 'Brno' pro uživatele: {user_name}")
else:
    print("\nMiroslav Zelený nenalezen v databázi")

conn.close()
print("Hotovo!")