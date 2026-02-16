import mysql.connector
from werkzeug.security import generate_password_hash

def setup_auth():
    print("Connecting to database...")
    conn = mysql.connector.connect(
        host="localhost", user="root", password="momdad@com", database="loan_database"
    )
    cursor = conn.cursor()

    # 1. Create USERS Table
    print("creating 'users' table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255)
    )
    """)

    # 2. Create ADMINS Table
    print("creating 'admins' table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(255)
    )
    """)

    # 3. Create a Default Admin (username: admin, password: admin123)
    admin_pass = generate_password_hash("admin123")
    try:
        cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", 
                       ("admin", admin_pass))
        print(" Default Admin created: User='admin', Pass='admin123'")
    except mysql.connector.Error:
        print(" Admin already exists.")

    conn.commit()
    cursor.close()
    conn.close()
    print(" Auth Database Ready!")

if __name__ == "__main__":
    setup_auth()