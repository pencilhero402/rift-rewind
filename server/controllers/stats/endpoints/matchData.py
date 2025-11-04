import sqlite3
import logging
import os
import json

from server.config.database import connect_to_database
from server.controllers.stats.endpoints.get_match_by_matchID import MatchByMatchID

from dotenv import load_dotenv
load_dotenv()

MATCH_DATA_PATH = os.getenv("MATCH_DATA_DIR")

class RiotAPIService:
    def get_match_data_by_match_id(self, matchId):
        a = MatchByMatchID(matchId)
        return a.load_response()

class MatchDataController:
    def __init__(self, matchId=None):
        self.matchId = matchId
        self.api_service = RiotAPIService()
        
    def getAllMatchData(self):
        conn, cursor = connect_to_database(MATCH_DATA_PATH)
        if conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
        if conn is None or cursor is None:
            logging.error("Failed to connect to the database.")
            return []
        try:
            cursor.execute("SELECT * FROM MatchData")
            rows = cursor.fetchall()
            matches = [dict(row) for row in rows]
            logging.info("Successfully retrieved MatchData table")
            return matches
        except sqlite3.Error as e:
            logging.error(f"Error getting Match Data from MatchData table: {e}")
            return []
        
    def createMatchData(self):
        conn, cursor = connect_to_database(MATCH_DATA_PATH)
        match_data = self.api_service.get_match_data_by_match_id(self.matchId)
        
        if not match_data:
            logging.error(f"No match data returned for matchId {self.matchId}")
            return
    
        if conn and cursor:
            try:
                cursor.execute('''
                        INSERT OR IGNORE INTO MatchData (matchId, matchData)
                        VALUES (?, ?)
                        ;
                    ''', (self.matchId, json.dumps(match_data),)
                    )
                conn.commit()
                logging.info(f"✅ Successfully inserted match {self.matchId} into MatchData")
            except sqlite3.Error as e:
                logging.error(f"Error inserting data into MatchData table: {e}")
            finally:
                conn.close()
        else:
            logging.error("Match data not fetched or database connection failed.")