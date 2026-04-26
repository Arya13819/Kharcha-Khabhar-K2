from flask import Flask, render_template, request, redirect, session, send_file, url_for
import csv
import io
from fpdf import FPDF
from datetime import datetime, date 
import mysql.connector

app = Flask(__name__)

app.secret_key = 'your_secret_key_here'  


# MySQL connection config
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="MYSQL@Secure!123",  
        database="user_db"             
    )

@app.route('/')
def home():
    return render_template('index.html')

# for home page
@app.route('/submit', methods=['POST'])
def submit():
    if 'user' not in session:
        return redirect(url_for('home', auth='required'))

    username = session['user']

    budget = request.form.get('budget')
    expense_date = request.form.get('date')
    payee = request.form.get('payee')
    transaction_type = request.form.get('transaction_type')
    amount = request.form.get('amount')
    payment_mode = request.form.get('payment_mode')
    category = request.form.get('category')

    # Budget (optional)
    budget = float(budget) if budget not in (None, "") else None

    # Amount (required)
    if amount in (None, ""):
        return redirect(url_for('home', error='amount_required'))
    amount = float(amount)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (username, budget, date, payee, transaction_type, amount, payment_mode, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (username, budget, expense_date, payee,
          transaction_type, amount, payment_mode, category))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('home', submitted='true'))

@app.route('/balance')
def balance():
    if 'user' not in session:
        return redirect(url_for('home', auth='required'))

    username = session['user']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Latest budget for this user
    cursor.execute("""
        SELECT budget
        FROM expenses
        WHERE username = %s AND budget IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
    """, (username,))
    row = cursor.fetchone()
    budget = float(row[0]) if row else 0

    # Total expenses
    cursor.execute("""
        SELECT IFNULL(SUM(amount), 0)
        FROM expenses
        WHERE username = %s AND transaction_type = 'Expense'
    """, (username,))
    total_expense = float(cursor.fetchone()[0])

    # Total income
    cursor.execute("""
        SELECT IFNULL(SUM(amount), 0)
        FROM expenses
        WHERE username = %s AND transaction_type = 'Income'
    """, (username,))
    total_income = float(cursor.fetchone()[0])

    remaining_balance = budget + total_income - total_expense

    cursor.close()
    conn.close()

    return render_template(
        'balance.html',
        budget=budget,
        income=total_income,
        expense=total_expense,
        balance=remaining_balance
    )



# for register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Capture the registration data from the form
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        gender = request.form.get('gender')
        contact = request.form.get('contact')
        security_key = request.form.get('security_key')
        city = request.form.get('city')

        # Convert empty middle name to NULL
        if middle_name == "":
            middle_name = None

        # Insert the user data into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (first_name, middle_name, last_name, email, username, password, gender, contact, security_key, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (first_name, middle_name, last_name, email, username, password, gender, contact, security_key, city)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('home', register='success'))

    return render_template('register.html')


# for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        login_time = datetime.now()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if the user exists and password is correct in the `users` table
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user'] = username

            # Log the successful login in the LOGIN table
            log_cursor = conn.cursor()
            log_cursor.execute("""
                INSERT INTO LOGIN (username, email, password, last_login, status)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE last_login = VALUES(last_login), status = 'Success'
            """, (username, user['email'], user['password'], login_time, 'Success'))
            conn.commit()

            log_cursor.close()
            cursor.close()
            conn.close()
            # return redirect(url_for('home', login='success'))
            return redirect(url_for('home') + '?login=success')


        else:
            # Log the failed login attempt
            log_cursor = conn.cursor()
            log_cursor.execute("""
                INSERT INTO LOGIN (username, email, password, last_login, status)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE last_login = VALUES(last_login), status = 'Failed'
            """, (username, '', password, login_time, 'Failed'))
            conn.commit()

            log_cursor.close()
            cursor.close()
            conn.close()
            return redirect(url_for('login', login='failed'))
        
    return render_template('login.html')

# for logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    # return redirect(url_for('home', logout='true'))
    return redirect(url_for('home') + '?logout=true')


# for history page
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('home', auth='required'))

    username = session['user']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT date, payee, transaction_type, amount, payment_mode, category, budget
        FROM expenses
        WHERE username = %s
        ORDER BY date DESC
    """, (username,))

    expenses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('history.html', expenses=expenses)


# for expense page
# @app.route("/expense", methods=["GET", "POST"])
# def expense():
#     if "user" not in session:
#         return redirect(url_for('home', auth='required'))

#     category_selected = None
#     expenses = []

#     if request.method == "POST":
#         category_selected = request.form.get("category")
#         username = session["user"]

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         query = """
#             SELECT * FROM expenses
#             WHERE username = %s AND category = %s
#         """
#         cursor.execute(query, (username, category_selected))
#         expenses = cursor.fetchall()

#         cursor.close()
#         conn.close()

#     return render_template("expense.html", expenses=expenses, category_selected=category_selected)

@app.route("/expense", methods=["GET", "POST"])
def expense():
    if "user" not in session:
        return redirect(url_for('home', auth='required'))

    category_selected = None
    expenses = []

    if request.method == "POST":
        category_selected = request.form.get("category")
        username = session["user"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT * FROM expenses
            WHERE username = %s AND category = %s AND transaction_type = 'Expense'
        """
        cursor.execute(query, (username, category_selected))
        expenses = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template("expense.html", expenses=expenses, category_selected=category_selected)


# for report page
class DashboardPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Financial Dashboard Report', border=False, ln=True, align='C')
        self.ln(5)

    def summary_section(self, income, expense, balance):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.cell(60, 10, f'Total Income: Rs.{income:.2f}', 1, 0, 'C', fill=True)
        self.cell(60, 10, f'Total Expense: Rs.{expense:.2f}', 1, 0, 'C', fill=True)
        self.cell(60, 10, f'Net Balance: Rs.{balance:.2f}', 1, 1, 'C', fill=True)
        self.ln(10)

    def table_section(self, data):
        headers = ["Date", "Payee", "Type", "Amount", "Mode", "Category", "Budget"]
        col_widths = [25, 30, 25, 25, 30, 30, 25]

        self.set_font("Arial", 'B', 10)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, border=1, align='C')
        self.ln()

        self.set_font("Arial", "", 10)
        for row in data:
            self.cell(col_widths[0], 10, str(row['date']), border=1)
            self.cell(col_widths[1], 10, row['payee'], border=1)
            self.cell(col_widths[2], 10, row['transaction_type'], border=1)
            self.cell(col_widths[3], 10, f"{row['amount']:.2f}", border=1)
            self.cell(col_widths[4], 10, row['payment_mode'], border=1)
            self.cell(col_widths[5], 10, row['category'], border=1)
            self.cell(col_widths[6], 10, f"{row['budget']:.2f}", border=1)
            self.ln()

@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'user' not in session:
        return redirect(url_for('home', auth='required'))

    if request.method == 'POST':
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')
        action = request.form.get('action')  # 'csv' or 'pdf'
        username = session['user']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT date, payee, transaction_type, amount, payment_mode, category, budget
            FROM expenses
            WHERE username = %s AND date BETWEEN %s AND %s
            ORDER BY date DESC
        """, (username, start_date, end_date))
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        # CSV export
        if action == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Date', 'Payee', 'Type', 'Amount', 'Mode', 'Category', 'Budget'])
            for row in data:
                formatted_date = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else str(row['date'])
                writer.writerow([
                    formatted_date,
                    row['payee'],
                    row['transaction_type'],
                    f"{row['amount']:.2f}",
                    row['payment_mode'],
                    row['category'],
                    f"{row['budget']:.2f}" if row['budget'] else "0.00"
                ])

            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                download_name='expense_report.csv',
                as_attachment=True
            )

        # PDF export
        elif action == 'pdf':
            total_expense = sum(x['amount'] for x in data if x['transaction_type'] == 'Expense')
            total_income = sum(x['amount'] for x in data if x['transaction_type'] == 'Income')
            net_balance = total_income - total_expense

            pdf = DashboardPDF()
            pdf.add_page()
            pdf.summary_section(total_income, total_expense, net_balance)
            pdf.table_section(data)

            # FPDF already returns bytes/bytearray; no need to encode
            pdf_bytes = pdf.output(dest="S")  # This is bytes

            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                download_name="financial_dashboard_report.pdf",
                as_attachment=True
            )

    return render_template("report.html")

# Route for Tips Page
@app.route('/tips')
def tips():
    return render_template('tips.html')

if __name__ == '__main__':
    app.run(debug=True)







# import os
# import csv
# import io
# from flask import Flask, render_template, request, redirect, session, send_file, url_for
# from fpdf import FPDF
# from datetime import datetime, date 
# from database import get_db_connection, get_cursor

# app = Flask(__name__)
# app.secret_key = 'your_secret_key_here' 

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/submit', methods=['POST'])
# def submit():
#     if 'user' not in session:
#         return redirect(url_for('home', auth='required'))

#     username = session['user']
#     budget = request.form.get('budget')
#     expense_date = request.form.get('date')
#     payee = request.form.get('payee')
#     transaction_type = request.form.get('transaction_type')
#     amount = request.form.get('amount')
#     payment_mode = request.form.get('payment_mode')
#     category = request.form.get('category')

#     budget = float(budget) if budget not in (None, "") else None
#     if amount in (None, ""):
#         return redirect(url_for('home', error='amount_required'))
#     amount = float(amount)

#     conn = get_db_connection()
#     cursor = conn.cursor() # Standard cursor for INSERTs
    
#     cursor.execute("""
#         INSERT INTO expenses
#         (username, budget, date, payee, transaction_type, amount, payment_mode, category)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#     """, (username, budget, expense_date, payee, transaction_type, amount, payment_mode, category))

#     conn.commit()
#     cursor.close()
#     conn.close()
#     return redirect(url_for('home', submitted='true'))

# @app.route('/balance')
# def balance():
#     if 'user' not in session:
#         return redirect(url_for('home', auth='required'))

#     username = session['user']
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     cursor.execute("SELECT budget FROM expenses WHERE username = %s AND budget IS NOT NULL ORDER BY id DESC LIMIT 1", (username,))
#     row = cursor.fetchone()
#     budget = float(row[0]) if row else 0

#     # Total expenses (Note: PostgreSQL uses COALESCE instead of IFNULL)
#     func = "COALESCE" if os.environ.get('DATABASE_URL') else "IFNULL"
    
#     cursor.execute(f"SELECT {func}(SUM(amount), 0) FROM expenses WHERE username = %s AND transaction_type = 'Expense'", (username,))
#     total_expense = float(cursor.fetchone()[0])

#     cursor.execute(f"SELECT {func}(SUM(amount), 0) FROM expenses WHERE username = %s AND transaction_type = 'Income'", (username,))
#     total_income = float(cursor.fetchone()[0])

#     remaining_balance = budget + total_income - total_expense
#     cursor.close()
#     conn.close()

#     return render_template('balance.html', budget=budget, income=total_income, expense=total_expense, balance=remaining_balance)

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         data = (
#             request.form.get('first_name'),
#             request.form.get('middle_name') or None,
#             request.form.get('last_name'),
#             request.form.get('email'),
#             request.form.get('username'),
#             request.form.get('password'),
#             request.form.get('gender'),
#             request.form.get('contact'),
#             request.form.get('security_key'),
#             request.form.get('city')
#         )

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO users (first_name, middle_name, last_name, email, username, password, gender, contact, security_key, city) 
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, data)
#         conn.commit()
#         cursor.close()
#         conn.close()
#         return redirect(url_for('home', register='success'))
#     return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#         conn = get_db_connection()
#         cursor = get_cursor(conn)

#         cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
#         user = cursor.fetchone()

#         if user:
#             session['user'] = username
#             log_cursor = conn.cursor()
#             # Handle MySQL "ON DUPLICATE KEY" vs PostgreSQL "ON CONFLICT"
#             if os.environ.get('DATABASE_URL'):
#                 log_cursor.execute("""
#                     INSERT INTO login (username, email, password, last_login, status)
#                     VALUES (%s, %s, %s, %s, %s)
#                     ON CONFLICT (username) DO UPDATE SET last_login = EXCLUDED.last_login, status = 'Success'
#                 """, (username, user['email'], user['password'], datetime.now(), 'Success'))
#             else:
#                 log_cursor.execute("""
#                     INSERT INTO LOGIN (username, email, password, last_login, status)
#                     VALUES (%s, %s, %s, %s, %s)
#                     ON DUPLICATE KEY UPDATE last_login = VALUES(last_login), status = 'Success'
#                 """, (username, user['email'], user['password'], datetime.now(), 'Success'))
#             conn.commit()
#             return redirect(url_for('home') + '?login=success')
#         else:
#             return redirect(url_for('login', login='failed'))
#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     session.pop('user', None)
#     return redirect(url_for('home') + '?logout=true')

# @app.route('/history')
# def history():
#     if 'user' not in session:
#         return redirect(url_for('home', auth='required'))
#     conn = get_db_connection()
#     cursor = get_cursor(conn)
#     cursor.execute("SELECT date, payee, transaction_type, amount, payment_mode, category, budget FROM expenses WHERE username = %s ORDER BY date DESC", (session['user'],))
#     expenses = cursor.fetchall()
#     cursor.close()
#     conn.close()
#     return render_template('history.html', expenses=expenses)

# # PDF/CSV Logic remains similar, using get_db_connection() and get_cursor()

# @app.route('/setup-db')
# def setup_db():
#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()
        
#         # SQL Commands to create your tables
#         sql_commands = """
#         CREATE TABLE IF NOT EXISTS users (
#             id SERIAL PRIMARY KEY,
#             first_name VARCHAR(50),
#             middle_name VARCHAR(50),
#             last_name VARCHAR(50),
#             email VARCHAR(100),
#             username VARCHAR(50) UNIQUE,
#             password VARCHAR(100),
#             gender VARCHAR(10),
#             contact VARCHAR(20),
#             security_key VARCHAR(50),
#             city VARCHAR(50)
#         );

#         CREATE TABLE IF NOT EXISTS expenses (
#             id SERIAL PRIMARY KEY,
#             username VARCHAR(50),
#             budget DECIMAL(10, 2),
#             date DATE,
#             payee VARCHAR(100),
#             transaction_type VARCHAR(20),
#             amount DECIMAL(10, 2),
#             payment_mode VARCHAR(50),
#             category VARCHAR(50)
#         );

#         CREATE TABLE IF NOT EXISTS login (
#             username VARCHAR(50) PRIMARY KEY,
#             email VARCHAR(100),
#             password VARCHAR(100),
#             last_login TIMESTAMP,
#             status VARCHAR(20)
#         );
#         """
#         cur.execute(sql_commands)
#         conn.commit()
#         cur.close()
#         conn.close()
#         return "Database tables created successfully! You can now register."
#     except Exception as e:
#         return f"Error creating tables: {str(e)}"


# if __name__ == '__main__':
#     app.run(debug=True)
