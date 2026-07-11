# K2 — Kharcha Khabhar Expense Tracker

A full-stack personal finance web app to track income, expenses, and budgets. Log transactions, visualize spending with interactive charts, filter history, and export reports as CSV or PDF.

**Live demo:** [https://kharcha-khabhar-k2.onrender.com]

## Features

- **Secure authentication** — passwords and security keys are bcrypt-hashed; all secrets loaded from environment variables; parameterized SQL queries throughout
- **Interactive dashboard** — spending-by-category doughnut chart and monthly income-vs-expense trend, powered by Chart.js
- **Full transaction management** — add, edit, and delete income/expense entries with budget tracking
- **Password recovery** — reset your password using the security key chosen at registration
- **Transaction history** — filter by All / Income / Expense with one click
- **Reports** — export any date range as CSV or a formatted PDF
- **Dual-database support** — runs on PostgreSQL in the cloud (Render) and MySQL locally, auto-detected via environment

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Gunicorn |
| Database | PostgreSQL (production) / MySQL (local) |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Auth | Flask-Bcrypt (password hashing) |
| Reports | FPDF (PDF), csv (CSV) |
| Hosting | Render |

## Run Locally

1. Clone the repo and install dependencies:
   ```bash
   git clone https://github.com/Arya13819/Kharcha-Khabhar-K2.git
   cd Kharcha-Khabhar-K2
   pip install -r requirements.txt
   ```
2. Create the MySQL database — run `sql/schema_mysql.sql` in MySQL.
3. Set your environment variables (PowerShell shown; use `export` on Mac/Linux):
   ```powershell
   $env:MYSQL_PASSWORD = "your-mysql-password"
   $env:SECRET_KEY = "any-long-random-string"
   ```
4. Start the app:
   ```bash
   python app.py
   ```
5. Open http://127.0.0.1:5000

## Deployment (Render)

1. Create a **PostgreSQL** instance on Render and copy its *Internal Database URL*.
2. Create a **Web Service** from this repo with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
3. Add environment variables: `DATABASE_URL`, `SECRET_KEY`, `SETUP_KEY`.
4. After the first deploy, visit `/setup-db?key=YOUR_SETUP_KEY` once to create the tables.

## Security Notes

- No credentials are committed to this repository — all secrets come from environment variables
- User passwords are never stored in plaintext (bcrypt with per-password salt)
- Login audit log records timestamps and status only — never passwords
- All database queries use parameterized statements to prevent SQL injection

## Author

**Arya Gupta** — [GitHub](https://github.com/Arya13819)
