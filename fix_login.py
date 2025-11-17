import bcrypt

# Test hash
password = "test123"
salt = bcrypt.gensalt()
hash_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

print(f"Password: {password}")
print(f"Salt: {salt}")
print(f"Hash: {hash_pw}")
print(f"Hash decoded: {hash_pw.decode('utf-8')}")

# Test verification
check1 = bcrypt.checkpw(password.encode('utf-8'), hash_pw)
check2 = bcrypt.checkpw(password.encode('utf-8'), hash_pw.decode('utf-8').encode('utf-8'))

print(f"Check 1: {check1}")
print(f"Check 2: {check2}")