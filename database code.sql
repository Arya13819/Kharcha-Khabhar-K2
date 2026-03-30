CREATE DATABASE user_db;
USE user_db;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    contact VARCHAR(20) NOT NULL,
    security_key VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL
);
describe users;
select * from users;

CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    budget DECIMAL(10,2),
    date DATE NOT NULL,
    payee VARCHAR(100) NOT NULL,
    transaction_type ENUM('Income', 'Expense') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_mode ENUM('Cash', 'Credit Card', 'Debit Card', 'Online Transfer') NOT NULL,
    category ENUM('Food', 'Transport', 'Shopping', 'Cosmetics', 'Others') NOT NULL
);
describe expenses;
select * from expenses;

ALTER TABLE expenses
ADD COLUMN username VARCHAR(100) NOT NULL;

ALTER TABLE expenses
ADD CONSTRAINT fk_expenses_user
FOREIGN KEY (username) REFERENCES users(username)
ON DELETE CASCADE;


CREATE TABLE LOGIN (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
describe LOGIN;
ALTER TABLE LOGIN
ADD COLUMN last_login DATETIME;
ALTER TABLE LOGIN
add column  status ENUM('Success', 'Failed') NOT NULL;
select * from LOGIN;

drop database user_db;