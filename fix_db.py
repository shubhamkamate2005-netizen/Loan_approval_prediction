import mysql.connector

try:
    print("Connecting to database...")
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="momdad@com", 
        database="loan_database"
    )
    cursor = conn.cursor()
    print("Connected to 'loan_database'.")

    print("Attempting to add missing columns...")
    
   
    queries = [
        "ALTER TABLE applicants ADD COLUMN state VARCHAR(50) AFTER address",
        "ALTER TABLE applicants ADD COLUMN district VARCHAR(50) AFTER state",
        "ALTER TABLE applicants ADD COLUMN taluk VARCHAR(50) AFTER district",
        "ALTER TABLE applicants ADD COLUMN bank_name VARCHAR(100) AFTER taluk"
    ]

    for q in queries:
        try:
            cursor.execute(q)
            print(f"Executed: {q}")
        except mysql.connector.Error as err:
            if "Duplicate column name" in str(err):
                print(f"Column already exists (Skipping): {err}")
            else:
                print(f"Error adding column: {err}")


    conn.commit()
    print("\n--- FINAL VERIFICATION ---")
    cursor.execute("DESCRIBE applicants")
    columns = [row[0] for row in cursor.fetchall()]
    
    if 'state' in columns and 'bank_name' in columns:
        print("success! Your table now has: State, District, Taluk, Bank Name.")
    else:
        print(" Failure. The columns are still missing.")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"CRITICAL ERROR: {e}")