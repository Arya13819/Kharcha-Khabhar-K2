-- K2 Expense Tracker: LOCAL development schema (MySQL)
-- Run this once in MySQL Workbench / CLI before running the app locally.

CREATE DATABASE IF NOT EXISTS user_db;
USE user_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,        -- stores bcrypt hash
    gender VARCHAR(20) NOT NULL,
    contact VARCHAR(20) NOT NULL,
    security_key VARCHAR(255) NOT NULL,    -- stores bcrypt hash
    city VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    budget DECIMAL(10,2),
    date DATE NOT NULL,
    payee VARCHAR(100) NOT NULL,
    transaction_type ENUM('Income', 'Expense') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_mode ENUM('Cash', 'Credit Card', 'Debit Card', 'Online Transfer') NOT NULL,
    category ENUM('Food', 'Transport', 'Shopping', 'Cosmetics', 'Others') NOT NULL,
    CONSTRAINT fk_expenses_user FOREIGN KEY (username)
        REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS login (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    password VARCHAR(255) NOT NULL DEFAULT '',  -- kept for legacy compatibility; never populated
    last_login DATETIME,
    status ENUM('Success', 'Failed')
);
