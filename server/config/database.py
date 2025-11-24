import logging
import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.DEBUG,  # Adjust the level to DEBUG, INFO, etc.
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Log to console
                        logging.FileHandler("app.log")  # Log to a file
                    ])

def connect_to_database(db_file):
    try:
        conn = mysql.connector.connect(
            host=os.getenv('RDS_HOST'),
            user=os.getenv('RDS_USER'),
            password=os.getenv('RDS_PASSWORD'),
            port=int(os.getenv('RDS_PORT', 3306)),
            database=db_file
        )
        cursor = conn.cursor()
        return conn, cursor
    except mysql.connector.Error as err:
        raise RuntimeError(f"Error connecting to database {db_file}: {err}")

    
def close_connection(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    
""" ----- Test database connection -----
conn, cursor = connect_to_database('mydatabase')
if cursor:
    cursor.execute("SELECT version()")
    result = cursor.fetchone()
    print(result)
close_connection(conn, cursor)
"""