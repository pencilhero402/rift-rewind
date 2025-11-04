import sqlite3
import logging
import database as db
logging.basicConfig(level=logging.INFO)

def createPlayersTable():
    """ ----- Creates the Players if it doesn't already exist ----- """
    conn, cursor = db.connect_to_database("../data/Player.db")
    
    if conn is None or cursor is None:
            logging.error("Failed to connect to the database. Aborting table creation.")
            return
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Player (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puuid TEXT NOT NULL UNIQUE,
                gameName TEXT,
                tagLine TEXT,
                server TEXT,
                summonerIconId INTEGER,
                summonerLevel INTEGER,
                tier TEXT
            );
        ''')    
        conn.commit()
        logging.info("✅ Successfully created Player table")
        
    except sqlite3.Error as e:
        logging.error(f"Error creating Player table: {e}")

    finally:
        # Close the connection
        db.close_connection(conn, cursor)
    
def createMatchesTable():
    """ ----- Creates the Match Table if it doesn't already exist ----- 
        Match = {
            matchId TEXT PRIMARY KEY,
            date TEXT
        }
    """
    conn, cursor = db.connect_to_database("../data/Match.db")
    
    if conn is None or cursor is None:
            logging.error("Failed to connect to the database. Aborting table creation.")
            return
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Match (
                matchId TEXT PRIMARY KEY,
                date TEXT
            );
        ''')    
        conn.commit()
        logging.info("⚔️ Successfully created Match table")
        
    except sqlite3.Error as e:
        logging.error(f"Error creating Match table: {e}")

    finally:
        # Close the connection
        db.close_connection(conn, cursor)

def createMatchDataTable():
    """ Create MatchData table if it doesn't already exist """
    conn, cursor = db.connect_to_database("../data/MatchData.db")
    if conn is None or cursor is None:
            logging.error("Failed to connect to the database. Aborting table creation.")
            return
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS MatchData (
                matchId TEXT PRIMARY KEY,
                matchData TEXT
            );
        ''')    
        conn.commit()
        logging.info("🐥 Successfully created MatchData table")
        
    except sqlite3.Error as e:
        logging.error(f"Error creating MatchData table: {e}")

    finally:
        # Close the connection
        db.close_connection(conn, cursor)

createPlayersTable()
createMatchesTable()
createMatchDataTable()