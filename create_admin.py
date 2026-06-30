import os
import mysql.connector
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', 'localhost'),
    'user':     os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'venuesync'),
}

username = input("Enter admin username: ")
password = input("Enter admin password: ")

hashed = generate_password_hash(password)

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute(
    'INSERT INTO users (username, password, role) VALUES (%s, %s, %s)',
    (username, hashed, 'admin')
)
conn.commit()
cursor.close()
conn.close()

print(f"Admin '{username}' created successfully.")
