-- v1.4 migration: add UPI payment mode (run once in MySQL Workbench)
-- (Render/PostgreSQL needs nothing - it uses VARCHAR, not ENUM)
USE user_db;

ALTER TABLE expenses
MODIFY COLUMN payment_mode
ENUM('Cash', 'Credit Card', 'Debit Card', 'Online Transfer', 'UPI') NOT NULL;

ALTER TABLE recurring_expenses
MODIFY COLUMN payment_mode
ENUM('Cash', 'Credit Card', 'Debit Card', 'Online Transfer', 'UPI') NOT NULL;
