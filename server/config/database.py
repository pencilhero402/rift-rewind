import sqlite3
import logging
import os

logging.basicConfig(level=logging.DEBUG,  # Adjust the level to DEBUG, INFO, etc.
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Log to console
                        logging.FileHandler("app.log")  # Log to a file
                    ])

def connect_to_database(db_file):
    """Create and return SQLite database connection"""
    try:
        if os.path.isdir(db_file):
            db_file = os.path.join('../data/', db_file)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        logging.info("Connection successful")
        return conn, cursor
    except sqlite3.Error as e: 
        logging.error(f"Error connecting to database: {e}")
        return None, None
    
def close_connection(conn, cursor):
    """Close cursor and connection to database"""
    try:
        cursor.close()
        conn.close()
        logging.info("Connection closed.")
    except sqlite3.Error as e:
        logging.error(f"Error closing the connection: {e}")

conn, cursor = connect_to_database("")
close_connection(conn, cursor)