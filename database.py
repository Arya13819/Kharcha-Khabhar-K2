# import mysql.connector

# def get_db_connection():
#     try:
#         conn = mysql.connector.connect(
#             host="localhost",
#             user="root",   # Replace with your MySQL username
#             password="MYSQL@Secure!123",  # Replace with your MySQL password
#             database="user_db"  # Replace with your database name
#         )
#         return conn
#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#         return None



# import os
# import mysql.connector
# import psycopg2  # For PostgreSQL on Render
# from urllib.parse import urlparse

# def get_db_connection():
#     # This looks for the variable you just added in your screenshot
#     db_url = os.environ.get('DATABASE_URL')

#     if db_url:
#         # If on Render, connect to PostgreSQL
#         return psycopg2.connect(db_url)
#     else:
#         # If on your PC (D: drive), connect to your local MySQL
#         return mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="MYSQL@Secure!123",
#             database="user_db"
#         )


import os
import mysql.connector
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    # Detects the Render Environment Variable
    db_url = os.environ.get('DATABASE_URL')

    if db_url:
        # Cloud Connection (PostgreSQL)
        conn = psycopg2.connect(db_url)
        return conn
    else:
        # Local Connection (MySQL)
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="MYSQL@Secure!123",  # Your local password
            database="user_db" 
        )

def get_cursor(conn):
    """Helper to get a dictionary-style cursor for both DB types"""
    if os.environ.get('DATABASE_URL'):
        # PostgreSQL uses RealDictCursor for dict-like results
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        # MySQL uses dictionary=True
        return conn.cursor(dictionary=True)