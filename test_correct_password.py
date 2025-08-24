import hashlib

# Správné heslo z testovacích dat
password = "heslo123"
password_hash = hashlib.sha256(password.encode()).hexdigest()

print(f"Heslo: {password}")
print(f"Hash: {password_hash}")

# Hash z databáze
db_hash = "b4240791ce0be7b92ddd5091ae67234e5dff778e786dc0a3cb9846af0cf8b653"
print(f"DB hash: {db_hash}")
print(f"Shodují se: {password_hash == db_hash}")