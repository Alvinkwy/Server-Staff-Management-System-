from werkzeug.security import generate_password_hash

users = [
    ("admin_ahmad", "Ahmad", 1),
    ("manager_siti", "Siti", 2),
    ("manager_chong", "Chong", 3),
    ("manager_arul", "Arul", 4),
    ("staff_sarah", "Sarah", 5),
    ("staff_muhammad", "Muhammad", 6),
    ("staff_ling", "Ling", 7),
    ("staff_fatimah", "Fatimah", 8),
    ("staff_ravi", "Ravi", 9),
    ("staff_emily", "Emily", 10),
]

def sql_escape(s: str) -> str:
    return s.replace("'", "''")

print("USE StaffManagementDB;")
print("GO")
print("INSERT INTO Users (Username, Password, StaffID) VALUES")

vals = []
for username, pwd, staffid in users:
    h = generate_password_hash(pwd)  # salted hash string
    vals.append(f"('{sql_escape(username)}', '{sql_escape(h)}', {staffid})")

print(",\n".join(vals) + ";")
print("GO")
