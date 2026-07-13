-- v1.6 migration: proper monthly budgets (run once in MySQL Workbench)
-- (On Render: re-visit /setup-db?key=... once after deploying)
USE user_db;

CREATE TABLE IF NOT EXISTS budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    month VARCHAR(7) NOT NULL,       -- 'YYYY-MM'
    amount DECIMAL(10,2) NOT NULL,
    UNIQUE KEY uq_user_month (username, month),
    CONSTRAINT fk_budgets_user FOREIGN KEY (username)
        REFERENCES users(username) ON DELETE CASCADE
);
