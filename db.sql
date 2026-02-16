CREATE DATABASE IF NOT EXISTS loan_database;
USE loan_database;

CREATE TABLE applicants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    dob DATE,
    district VARCHAR(50),
    state VARCHAR(50),
    bank_name VARCHAR(100),
    address TEXT,
    purpose VARCHAR(50),
    applicant_income DECIMAL(10,2),
    coapplicant_income DECIMAL(10,2),
    loan_amount DECIMAL(10,2),
    term INT,
    credit_history FLOAT,
    property_area VARCHAR(20),
    loan_status VARCHAR(20),
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 2. CREATE ADMIN TABLE (If not exists)
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(50)
);

-- 3. CREATE ADMIN USER (Ignore error if admin already exists)
INSERT IGNORE INTO admins (username, password) VALUES ('admin', 'admin123');

SELECT "Database Reset Successful!" AS Status;