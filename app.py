"""
K2 - Kharcha Khabhar Expense Tracker
Flask app: track income/expenses, budgets, history, reports (CSV/PDF),
dashboard with charts, and secure authentication (bcrypt-hashed passwords).

Runs on PostgreSQL in the cloud (Render) and MySQL locally.
"""

import os
import csv
import io
from datetime import datetime, date

from flask import (
    Flask, render_template, request, redirect, session, send_file,
    url_for, jsonify, abort
)
from flask_bcrypt import Bcrypt
from fpdf import FPDF

from database import (
    get_db_connection, get_cursor, month_expr, create_tables, IS_POSTGRES
)
from recurring import recurring_bp

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.register_blueprint(recurring_bp)

# Secret key comes from the environment in production (never hardcode it).
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key-change-me")

CATEGORIES = ["Food", "Groceries", "Transport", "Shopping", "Bills & Recharge", "Rent/Housing", "Health", "Entertainment", "Education", "Cosmetics", "Others"]


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def check_secret(stored_value, provided_value):
    """
    Verify a bcrypt-hashed value. Falls back to a plain comparison for
    accounts created before hashing was introduced (legacy rows).
    Returns (matches: bool, needs_rehash: bool).
    """
    if not stored_value:
        return False, False
    try:
        if bcrypt.check_password_hash(stored_value, provided_value):
            return True, False
    except (ValueError, TypeError):
        pass  # stored value is not a valid bcrypt hash -> legacy plaintext
    if stored_value == provided_value:
        return True, True  # matched as plaintext; should be upgraded to a hash
    return False, False


def login_required():
    return "user" not in session


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    if login_required():
        return redirect(url_for("home", auth="required"))

    username = session["user"]

    budget = request.form.get("budget")
    expense_date = request.form.get("date")
    payee = request.form.get("payee")
    transaction_type = request.form.get("transaction_type")
    amount = request.form.get("amount")
    payment_mode = request.form.get("payment_mode")
    category = request.form.get("category")

    try:
        budget = float(budget) if budget not in (None, "") else None
        amount = float(amount)
    except (TypeError, ValueError):
        return redirect(url_for("home", error="amount_required"))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO expenses
            (username, budget, date, payee, transaction_type, amount, payment_mode, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (username, budget, expense_date, payee,
             transaction_type, amount, payment_mode, category),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        cursor.close()
        conn.close()
        session.pop("user", None)  # stale session for a deleted user
        return redirect(url_for("home", auth="required"))
    cursor.close()
    conn.close()

    return redirect(url_for("home", submitted="true"))


@app.route("/balance")
def balance():
    if login_required():
        return redirect(url_for("home", auth="required"))

    username = session["user"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT budget FROM expenses
        WHERE username = %s AND budget IS NOT NULL
        ORDER BY id DESC LIMIT 1
        """,
        (username,),
    )
    row = cursor.fetchone()
    budget = float(row[0]) if row else 0

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) FROM expenses
        WHERE username = %s AND transaction_type = 'Expense'
        """,
        (username,),
    )
    total_expense = float(cursor.fetchone()[0])

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) FROM expenses
        WHERE username = %s AND transaction_type = 'Income'
        """,
        (username,),
    )
    total_income = float(cursor.fetchone()[0])

    remaining_balance = budget + total_income - total_expense

    cursor.close()
    conn.close()

    return render_template(
        "balance.html",
        budget=budget,
        income=total_income,
        expense=total_expense,
        balance=remaining_balance,
    )


# ---------------------------------------------------------------------------
# Registration / Login / Logout / Forgot password
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        password_hash = bcrypt.generate_password_hash(
            request.form.get("password")).decode("utf-8")
        key_hash = bcrypt.generate_password_hash(
            request.form.get("security_key")).decode("utf-8")

        data = (
            request.form.get("first_name"),
            request.form.get("middle_name") or None,
            request.form.get("last_name"),
            request.form.get("email"),
            request.form.get("username"),
            password_hash,
            request.form.get("gender"),
            request.form.get("contact"),
            key_hash,
            request.form.get("city"),
        )

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users
                (first_name, middle_name, last_name, email, username,
                 password, gender, contact, security_key, city)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                data,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            cursor.close()
            conn.close()
            return redirect(url_for("register", register="failed"))

        cursor.close()
        conn.close()
        return redirect(url_for("home", register="success"))

    return render_template("register.html")


def log_login(conn, username, email, status):
    """Record the latest login attempt (no passwords are ever stored)."""
    cur = conn.cursor()
    now = datetime.now()
    if IS_POSTGRES:
        cur.execute(
            """
            INSERT INTO login (username, email, last_login, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username)
            DO UPDATE SET last_login = EXCLUDED.last_login,
                          status = EXCLUDED.status
            """,
            (username, email, now, status),
        )
    else:
        cur.execute(
            """
            INSERT INTO login (username, email, password, last_login, status)
            VALUES (%s, %s, '', %s, %s)
            ON DUPLICATE KEY UPDATE last_login = VALUES(last_login),
                                    status = VALUES(status)
            """,
            (username, email, now, status),
        )
    conn.commit()
    cur.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        matches, needs_rehash = (False, False)
        if user:
            matches, needs_rehash = check_secret(user["password"], password)

        if matches:
            session["user"] = username

            # Transparently upgrade old plaintext passwords to bcrypt hashes
            if needs_rehash:
                new_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                up = conn.cursor()
                up.execute("UPDATE users SET password = %s WHERE username = %s",
                           (new_hash, username))
                conn.commit()
                up.close()

            log_login(conn, username, user["email"], "Success")
            conn.close()
            return redirect(url_for("home") + "?login=success")
        else:
            if user:
                log_login(conn, username, user["email"], "Failed")
            conn.close()
            return redirect(url_for("login", login="failed"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home") + "?logout=true")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username")
        security_key = request.form.get("security_key")
        new_password = request.form.get("new_password")

        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            conn.close()
            return redirect(url_for("forgot_password", reset="failed"))

        matches, _ = check_secret(user["security_key"], security_key)
        if not matches:
            conn.close()
            return redirect(url_for("forgot_password", reset="failed"))

        new_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = %s WHERE username = %s",
                    (new_hash, username))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("login", reset="success"))

    return render_template("forgot_password.html")


# ---------------------------------------------------------------------------
# History + Edit / Delete
# ---------------------------------------------------------------------------

@app.route("/history")
def history():
    if login_required():
        return redirect(url_for("home", auth="required"))

    username = session["user"]
    PER_PAGE = 20

    # --- Filters from query string ---
    q = request.args.get("q", "").strip()
    month = request.args.get("month", "").strip()
    category = request.args.get("category", "").strip()
    ttype = request.args.get("type", "").strip()
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    where = ["username = %s"]
    params = [username]
    if q:
        where.append("LOWER(payee) LIKE %s")
        params.append(f"%{q.lower()}%")
    if month:
        where.append(f"{month_expr('date')} = %s")
        params.append(month)
    if category in CATEGORIES:
        where.append("category = %s")
        params.append(category)
    if ttype in ("Income", "Expense"):
        where.append("transaction_type = %s")
        params.append(ttype)
    where_sql = " AND ".join(where)

    conn = get_db_connection()
    cursor = get_cursor(conn)

    # Months that actually have data (for the dropdown)
    cursor.execute(
        f"SELECT DISTINCT {month_expr('date')} AS m FROM expenses "
        "WHERE username = %s ORDER BY m DESC",
        (username,),
    )
    months = [r["m"] for r in cursor.fetchall()]

    # Total matching rows -> page count
    cursor.execute(
        f"SELECT COUNT(*) AS cnt FROM expenses WHERE {where_sql}",
        tuple(params),
    )
    total = int(cursor.fetchone()["cnt"])
    total_pages = max(1, -(-total // PER_PAGE))  # ceil division
    page = min(page, total_pages)

    cursor.execute(
        f"""
        SELECT id, date, payee, transaction_type, amount,
               payment_mode, category, budget
        FROM expenses
        WHERE {where_sql}
        ORDER BY date DESC, id DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params) + (PER_PAGE, (page - 1) * PER_PAGE),
    )
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        expenses=expenses,
        months=months,
        categories=CATEGORIES,
        q=q, month=month, category=category, ttype=ttype,
        page=page, total_pages=total_pages, total=total,
    )


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if login_required():
        return redirect(url_for("home", auth="required"))

    username = session["user"]
    conn = get_db_connection()

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount"))
            budget = request.form.get("budget")
            budget = float(budget) if budget not in (None, "") else None
        except (TypeError, ValueError):
            conn.close()
            return redirect(url_for("history", updated="failed"))

        cur = conn.cursor()
        cur.execute(
            """
            UPDATE expenses
            SET date = %s, payee = %s, transaction_type = %s, amount = %s,
                payment_mode = %s, category = %s, budget = %s
            WHERE id = %s AND username = %s
            """,
            (request.form.get("date"), request.form.get("payee"),
             request.form.get("transaction_type"), amount,
             request.form.get("payment_mode"), request.form.get("category"),
             budget, expense_id, username),
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("history", updated="true"))

    cursor = get_cursor(conn)
    cursor.execute(
        "SELECT * FROM expenses WHERE id = %s AND username = %s",
        (expense_id, username),
    )
    expense = cursor.fetchone()
    cursor.close()
    conn.close()

    if not expense:
        abort(404)
    return render_template("edit.html", expense=expense)


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if login_required():
        return redirect(url_for("home", auth="required"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM expenses WHERE id = %s AND username = %s",
        (expense_id, session["user"]),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("history", deleted="true"))


# ---------------------------------------------------------------------------
# Expense-by-category page
# ---------------------------------------------------------------------------

@app.route("/expense", methods=["GET", "POST"])
def expense():
    if login_required():
        return redirect(url_for("home", auth="required"))

    category_selected = None
    expenses = []

    if request.method == "POST":
        category_selected = request.form.get("category")
        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT * FROM expenses
            WHERE username = %s AND category = %s
              AND transaction_type = 'Expense'
            ORDER BY date DESC
            """,
            (session["user"], category_selected),
        )
        expenses = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template("expense.html", expenses=expenses,
                           category_selected=category_selected)


# ---------------------------------------------------------------------------
# Dashboard + chart data API
# ---------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    if login_required():
        return redirect(url_for("home", auth="required"))
    return render_template("dashboard.html")


@app.route("/api/chart-data")
def chart_data():
    if login_required():
        return jsonify({"error": "auth required"}), 401

    username = session["user"]
    conn = get_db_connection()
    cursor = get_cursor(conn)

    # Spending by category (expenses only)
    cursor.execute(
        """
        SELECT category, COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE username = %s AND transaction_type = 'Expense'
        GROUP BY category
        ORDER BY total DESC
        """,
        (username,),
    )
    cat_rows = cursor.fetchall()

    # Monthly income vs expense
    m = month_expr("date")
    cursor.execute(
        f"""
        SELECT {m} AS month,
               COALESCE(SUM(CASE WHEN transaction_type = 'Income'
                                 THEN amount ELSE 0 END), 0) AS income,
               COALESCE(SUM(CASE WHEN transaction_type = 'Expense'
                                 THEN amount ELSE 0 END), 0) AS expense
        FROM expenses
        WHERE username = %s
        GROUP BY {m}
        ORDER BY month
        """,
        (username,),
    )
    month_rows = cursor.fetchall()

    # Summary numbers
    cursor.execute(
        """
        SELECT
          COALESCE(SUM(CASE WHEN transaction_type = 'Income'
                            THEN amount ELSE 0 END), 0) AS income,
          COALESCE(SUM(CASE WHEN transaction_type = 'Expense'
                            THEN amount ELSE 0 END), 0) AS expense,
          COUNT(*) AS txn_count
        FROM expenses
        WHERE username = %s
        """,
        (username,),
    )
    summary = cursor.fetchone()

    # Budget status: latest budget vs this month's spending
    cursor.execute(
        """
        SELECT budget FROM expenses
        WHERE username = %s AND budget IS NOT NULL
        ORDER BY id DESC LIMIT 1
        """,
        (username,),
    )
    brow = cursor.fetchone()
    budget_amt = float(brow["budget"]) if brow else 0.0

    cursor.execute(
        f"""
        SELECT COALESCE(SUM(amount), 0) AS spent
        FROM expenses
        WHERE username = %s AND transaction_type = 'Expense'
          AND {m} = %s
        """,
        (username, date.today().strftime("%Y-%m")),
    )
    spent_this_month = float(cursor.fetchone()["spent"])

    cursor.close()
    conn.close()

    return jsonify({
        "budget_status": {
            "budget": budget_amt,
            "spent": spent_this_month,
            "percent": round(spent_this_month / budget_amt * 100, 1) if budget_amt > 0 else None,
        },
        "categories": {
            "labels": [r["category"] for r in cat_rows],
            "values": [float(r["total"]) for r in cat_rows],
        },
        "monthly": {
            "labels": [r["month"] for r in month_rows],
            "income": [float(r["income"]) for r in month_rows],
            "expense": [float(r["expense"]) for r in month_rows],
        },
        "summary": {
            "income": float(summary["income"]),
            "expense": float(summary["expense"]),
            "balance": float(summary["income"]) - float(summary["expense"]),
            "count": int(summary["txn_count"]),
        },
    })


# ---------------------------------------------------------------------------
# Reports (CSV / PDF)
# ---------------------------------------------------------------------------

class DashboardPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Financial Dashboard Report", border=False,
                  ln=True, align="C")
        self.ln(5)

    def summary_section(self, income, expense, balance):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(240, 240, 240)
        self.cell(60, 10, f"Total Income: Rs.{income:.2f}", 1, 0, "C", fill=True)
        self.cell(60, 10, f"Total Expense: Rs.{expense:.2f}", 1, 0, "C", fill=True)
        self.cell(60, 10, f"Net Balance: Rs.{balance:.2f}", 1, 1, "C", fill=True)
        self.ln(10)

    def table_section(self, data):
        headers = ["Date", "Payee", "Type", "Amount", "Mode", "Category", "Budget"]
        col_widths = [25, 30, 25, 25, 30, 30, 25]

        self.set_font("Arial", "B", 10)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, border=1, align="C")
        self.ln()

        self.set_font("Arial", "", 10)
        for row in data:
            budget_val = row["budget"] if row["budget"] else 0
            self.cell(col_widths[0], 10, str(row["date"]), border=1)
            self.cell(col_widths[1], 10, str(row["payee"]), border=1)
            self.cell(col_widths[2], 10, str(row["transaction_type"]), border=1)
            self.cell(col_widths[3], 10, f"{float(row['amount']):.2f}", border=1)
            self.cell(col_widths[4], 10, str(row["payment_mode"]), border=1)
            self.cell(col_widths[5], 10, str(row["category"]), border=1)
            self.cell(col_widths[6], 10, f"{float(budget_val):.2f}", border=1)
            self.ln()


@app.route("/report", methods=["GET", "POST"])
def report():
    if login_required():
        return redirect(url_for("home", auth="required"))

    if request.method == "POST":
        start_date = request.form.get("start-date")
        end_date = request.form.get("end-date")
        action = request.form.get("action")  # 'csv' or 'pdf'
        username = session["user"]

        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT date, payee, transaction_type, amount,
                   payment_mode, category, budget
            FROM expenses
            WHERE username = %s AND date BETWEEN %s AND %s
            ORDER BY date DESC
            """,
            (username, start_date, end_date),
        )
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        if action == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date", "Payee", "Type", "Amount",
                             "Mode", "Category", "Budget"])
            for row in data:
                formatted_date = (row["date"].strftime("%Y-%m-%d")
                                  if isinstance(row["date"], (datetime, date))
                                  else str(row["date"]))
                writer.writerow([
                    formatted_date,
                    row["payee"],
                    row["transaction_type"],
                    f"{float(row['amount']):.2f}",
                    row["payment_mode"],
                    row["category"],
                    f"{float(row['budget']):.2f}" if row["budget"] else "0.00",
                ])
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode("utf-8")),
                mimetype="text/csv",
                download_name="expense_report.csv",
                as_attachment=True,
            )

        elif action == "pdf":
            total_expense = sum(float(x["amount"]) for x in data
                                if x["transaction_type"] == "Expense")
            total_income = sum(float(x["amount"]) for x in data
                               if x["transaction_type"] == "Income")
            net_balance = total_income - total_expense

            pdf = DashboardPDF()
            pdf.add_page()
            pdf.summary_section(total_income, total_expense, net_balance)
            pdf.table_section(data)

            pdf_output = pdf.output(dest="S")
            pdf_bytes = (pdf_output.encode("latin-1")
                         if isinstance(pdf_output, str) else bytes(pdf_output))

            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                download_name="financial_dashboard_report.pdf",
                as_attachment=True,
            )

    return render_template("report.html")


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

@app.route("/tips")
def tips():
    return render_template("tips.html")


@app.route("/setup-db")
def setup_db():
    """One-time table creation on Render. Protected by SETUP_KEY env var."""
    if not IS_POSTGRES:
        return "setup-db is only for the cloud (PostgreSQL) database.", 400

    key = request.args.get("key", "")
    if key != os.environ.get("SETUP_KEY", ""):
        abort(403)

    try:
        create_tables()
        return "Database tables created successfully. You can now register!"
    except Exception as e:
        return f"Error creating tables: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
