"""
Recurring Transactions (v1.2) - Flask Blueprint.

Lets users define rules like "Rent, 8000, Monthly, next due 1st".
When a rule's next_due date arrives, the dashboard shows a reminder
and the user confirms with one click (no silent auto-adding, so no
accidental duplicates). Confirming inserts the transaction and
advances next_due by one period.

Wire-up in app.py (2 lines):
    from recurring import recurring_bp
    app.register_blueprint(recurring_bp)
"""

from datetime import date, timedelta

from flask import (
    Blueprint, render_template, request, redirect, session,
    url_for, jsonify
)

from database import get_db_connection, get_cursor

recurring_bp = Blueprint("recurring", __name__)

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def advance_due_date(d, frequency):
    """Return the next due date after one period, handling month-end safely
    (e.g. Jan 31 + Monthly -> Feb 28/29, not an invalid date)."""
    if frequency == "Weekly":
        return d + timedelta(days=7)

    if frequency == "Yearly":
        try:
            return d.replace(year=d.year + 1)
        except ValueError:  # Feb 29 -> Feb 28 next year
            return d.replace(year=d.year + 1, day=28)

    # Monthly (default)
    month = d.month + 1
    year = d.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    max_day = DAYS_IN_MONTH[month - 1]
    if month == 2 and _is_leap(year):
        max_day = 29
    return date(year, month, min(d.day, max_day))


def _login_required():
    return "user" not in session


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@recurring_bp.route("/recurring")
def recurring():
    if _login_required():
        return redirect(url_for("home", auth="required"))

    conn = get_db_connection()
    cursor = get_cursor(conn)
    cursor.execute(
        """
        SELECT id, payee, transaction_type, amount, payment_mode,
               category, frequency, next_due, active
        FROM recurring_expenses
        WHERE username = %s
        ORDER BY next_due ASC, id ASC
        """,
        (session["user"],),
    )
    rules = cursor.fetchall()
    cursor.close()
    conn.close()

    today = date.today()
    return render_template("recurring.html", rules=rules, today=today)


@recurring_bp.route("/recurring/add", methods=["POST"])
def recurring_add():
    if _login_required():
        return redirect(url_for("home", auth="required"))

    try:
        amount = float(request.form.get("amount"))
    except (TypeError, ValueError):
        return redirect(url_for("recurring.recurring", saved="failed"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO recurring_expenses
        (username, payee, transaction_type, amount, payment_mode,
         category, frequency, next_due)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (session["user"],
         request.form.get("payee"),
         request.form.get("transaction_type"),
         amount,
         request.form.get("payment_mode"),
         request.form.get("category"),
         request.form.get("frequency"),
         request.form.get("next_due")),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("recurring.recurring", saved="true"))


@recurring_bp.route("/recurring/toggle/<int:rule_id>", methods=["POST"])
def recurring_toggle(rule_id):
    """Pause or resume a rule."""
    if _login_required():
        return redirect(url_for("home", auth="required"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE recurring_expenses SET active = NOT active "
        "WHERE id = %s AND username = %s",
        (rule_id, session["user"]),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("recurring.recurring"))


@recurring_bp.route("/recurring/delete/<int:rule_id>", methods=["POST"])
def recurring_delete(rule_id):
    if _login_required():
        return redirect(url_for("home", auth="required"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM recurring_expenses WHERE id = %s AND username = %s",
        (rule_id, session["user"]),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("recurring.recurring", deleted_rule="true"))


# ---------------------------------------------------------------------------
# Due reminders (dashboard integration)
# ---------------------------------------------------------------------------

@recurring_bp.route("/api/due-recurring")
def due_recurring():
    """Rules that are active and due today or earlier."""
    if _login_required():
        return jsonify({"error": "auth required"}), 401

    conn = get_db_connection()
    cursor = get_cursor(conn)
    cursor.execute(
        """
        SELECT id, payee, transaction_type, amount, category,
               frequency, next_due
        FROM recurring_expenses
        WHERE username = %s AND active = TRUE AND next_due <= %s
        ORDER BY next_due ASC
        """,
        (session["user"], date.today()),
    )
    due = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({
        "due": [
            {
                "id": r["id"],
                "payee": r["payee"],
                "transaction_type": r["transaction_type"],
                "amount": float(r["amount"]),
                "category": r["category"],
                "frequency": r["frequency"],
                "next_due": str(r["next_due"]),
            }
            for r in due
        ]
    })


@recurring_bp.route("/recurring/confirm/<int:rule_id>", methods=["POST"])
def recurring_confirm(rule_id):
    """User confirmed a due reminder: insert the transaction on the due
    date and advance next_due by one period."""
    if _login_required():
        return redirect(url_for("home", auth="required"))

    username = session["user"]
    conn = get_db_connection()
    cursor = get_cursor(conn)
    cursor.execute(
        "SELECT * FROM recurring_expenses WHERE id = %s AND username = %s",
        (rule_id, username),
    )
    rule = cursor.fetchone()
    cursor.close()

    if not rule or not rule["active"]:
        conn.close()
        return redirect(url_for("dashboard"))

    due_date = rule["next_due"]

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO expenses
        (username, budget, date, payee, transaction_type, amount,
         payment_mode, category)
        VALUES (%s, NULL, %s, %s, %s, %s, %s, %s)
        """,
        (username, due_date, rule["payee"], rule["transaction_type"],
         rule["amount"], rule["payment_mode"], rule["category"]),
    )
    cur.execute(
        "UPDATE recurring_expenses SET next_due = %s "
        "WHERE id = %s AND username = %s",
        (advance_due_date(due_date, rule["frequency"]), rule_id, username),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("dashboard", recurring_added="true"))
