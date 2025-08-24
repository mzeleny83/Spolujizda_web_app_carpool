import hashlib

# Hash z databáze
db_hash = "b4240791ce0be7b92ddd5091ae67234e5dff778e786dc0a3cb9846af0cf8b653"

# Zkusím běžná hesla
passwords = ["password", "123456", "test", "admin", "heslo", "password123", "test123"]

print(f"Hledám heslo pro hash: {db_hash}")

for pwd in passwords:
    test_hash = hashlib.sha256(pwd.encode()).hexdigest()
    print(f"Heslo '{pwd}' -> {test_hash}")
    if test_hash == db_hash:
        print(f"✅ NALEZENO! Heslo je: {pwd}")
        break
else:
    print("❌ Heslo nenalezeno v seznamu")