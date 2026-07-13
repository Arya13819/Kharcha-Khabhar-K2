-- v1.5 migration: expanded categories (run once in MySQL Workbench)
-- (Render/PostgreSQL needs nothing - VARCHAR accepts new values automatically)
USE user_db;

ALTER TABLE expenses
MODIFY COLUMN category
ENUM('Food', 'Groceries', 'Transport', 'Shopping', 'Bills & Recharge',
     'Rent/Housing', 'Health', 'Entertainment', 'Education',
     'Cosmetics', 'Others') NOT NULL;

ALTER TABLE recurring_expenses
MODIFY COLUMN category
ENUM('Food', 'Groceries', 'Transport', 'Shopping', 'Bills & Recharge',
     'Rent/Housing', 'Health', 'Entertainment', 'Education',
     'Cosmetics', 'Others') NOT NULL;
