"""
Database layer for K2 Expense Tracker.

Works with TWO databases automatically:
  - On Render (cloud):  PostgreSQL  -> detected via the DATABASE_URL env variable
  - On your PC (local): MySQL       -> used when DATABASE_URL is not set

No passwords are hardcoded here. Locally, set the MYSQL_PASSWORD
environment variable before running the app.
"""

import os

# True when running on Render (or anywhere DATABASE_URL is set)
IS_POSTGRES = bool(os.environ.get("DATABASE_URL"))


def get_db_connection():
    """Return a database connection for the current environment."""
    if IS_POSTGRES:
        import psycopg2
        return psycopg2.connect(os.environ["DATABASE_URL"])
    else:
        import mysql.connector
        return mysql.connector.connect(
            host=os.environ.get("MYSQL_HOST", "localhost"),
            user=os.environ.get("MYSQL_USER", "root"),
            password=os.environ.get("MYSQL_PASSWORD", ""),
            database=os.environ.get("MYSQL_DB", "user_db"),
        )


def get_cursor(conn):
    """Return a dictionary-style cursor (rows behave like dicts) for both DBs."""
    if IS_POSTGRES:
        from psycopg2.extras import RealDictCursor
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor(dictionary=True)


def month_expr(column="date"):
    """SQL expression that formats a date as 'YYYY-MM' in either dialect."""
    if IS_POSTGRES:
        return f"TO_CHAR({column}, 'YYYY-MM')"
    else:
        return f"DATE_FORMAT({column}, '%Y-%m')"


# ---------------------------------------------------------------------------
# Table creation (used by the one-time /setup-db route on Render)
# ---------------------------------------------------------------------------

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    contact VARCHAR(20) NOT NULL,
    security_key VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    budget DECIMAL(10,2),
    date DATE NOT NULL,
    payee VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_mode VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS login (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    last_login TIMESTAMP,
    status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    month VARCHAR(7) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    UNIQUE (username, month)
);

CREATE TABLE IF NOT EXISTS recurring_expenses (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    payee VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL DEFAULT 'Expense',
    amount DECIMAL(10,2) NOT NULL,
    payment_mode VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    next_due DATE NOT NULL,
    active BOOLEAN DEFAULT TRUE
);
"""


def create_tables():
    """Create all tables (PostgreSQL). Safe to run more than once."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(POSTGRES_SCHEMA)
    conn.commit()
    cur.close()
    conn.close()
