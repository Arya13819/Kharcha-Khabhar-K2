-- v1.2 migration: recurring transactions (run once in MySQL Workbench)
USE user_db;

CREATE TABLE IF NOT EXISTS recurring_expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    payee VARCHAR(100) NOT NULL,
    transaction_type ENUM('Income', 'Expense') NOT NULL DEFAULT 'Expense',
    amount DECIMAL(10,2) NOT NULL,
    payment_mode ENUM('Cash', 'Credit Card', 'Debit Card', 'Online Transfer') NOT NULL,
    category ENUM('Food', 'Transport', 'Shopping', 'Cosmetics', 'Others') NOT NULL,
    frequency ENUM('Weekly', 'Monthly', 'Yearly') NOT NULL,
    next_due DATE NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_recurring_user FOREIGN KEY (username)
        REFERENCES users(username) ON DELETE CASCADE
);
USE user_db;
SHOW TABLES;