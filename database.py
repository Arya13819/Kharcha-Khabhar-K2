import mysql.connector

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",   # Replace with your MySQL username
            password="MYSQL@Secure!123",  # Replace with your MySQL password
            database="user_db"  # Replace with your database name
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None