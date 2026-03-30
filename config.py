import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.environ.get("DB_PASSWORD", "MySQL@Secure!123"),  # Use environment variable for security
    "database": "user_db"
}