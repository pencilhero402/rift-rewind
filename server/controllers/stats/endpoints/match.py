import sqlite3
import logging
import os
import json
from datetime import datetime

from server.config.database import connect_to_database
from server.controllers.stats.endpoints.get_account_by_riot_id import AccountByRiotID
from server.controllers.stats.endpoints.get_list_of_matchID_by_puuid import MatchIDsByPUUID
from server.controllers.stats.endpoints.get_match_by_matchID import MatchByMatchID

from server.controllers.stats.endpoints.matchData import MatchDataController

from dotenv import load_dotenv
load_dotenv()

MATCH_PATH = os.getenv("MATCHES_DIR")
# Queue Type Ids: https://static.developer.riotgames.com/docs/lol/queues.json
# Clash ID: 700 & ARAM Clash ID: 720

# -------- Move this to a Utils Class in another file EVENTUALLY --------
def convertUnixTimestamp(unix_time: int):
    # Convert to seconds
    timestamp_s = unix_time / 1000
    
    # Convert to datetime
    dt = datetime.fromtimestamp(timestamp_s)
    return dt.strftime("%B %d, %Y, %H:%M:%S")



class RiotAPIService:
    def get_account_by_riot_id(self, gameName, tagLine):
        a = AccountByRiotID(gameName, tagLine)
        return a.load_response()
    
    def get_matches_by_puuid(self, puuid, queueId):
        """ Returns an array of matchIds"""
        a = MatchIDsByPUUID(puuid=puuid,queue=queueId,start=0,count=100)
        a.load_response()
        return a
    
    def get_match_data_by_matchId(self, matchId):
        a = MatchDataController(matchId).createMatchData()
        return a
    
    def get_match_date_by_match_id(self, matchId):
        a = MatchByMatchID(matchId).get_dict()
        res = a["info"]["gameCreation"]
        return res

class MatchController:
    def __init__(self, gameName=None, tagLine=None, puuid=None, queueId=700):
        self.gameName = gameName
        self.tagLine = tagLine
        self.puuid = puuid
        self.queueId=queueId
        self.match_ids = []
        self.api_service = RiotAPIService()
    
    # Fetch matches given Player's name & tag
    def fetchMatches(self):
        # Step 1: Fetch account data (this gives us the puuid)
        if self.gameName and self.tagLine:
            account_data = self.api_service.get_account_by_riot_id(self.gameName, self.tagLine)
        else:
            print("No gameName or tagLine")
            return None
        
        if isinstance(account_data, dict):
            self.puuid = account_data.get("puuid", None)
            
        if self.puuid:
            # Step 2: Fetch matchIds from Player
            match_ids = self.api_service.get_matches_by_puuid(puuid=self.puuid, queueId=self.queueId).get_json()

            # Step 3: Process results
            if isinstance(match_ids, list):
                self.match_ids = match_ids
                return match_ids
        else:
            print("Error: PUUID not found, cannot fetch matchIds.")
            return None
    
    # Creates matches fetched from Player -> Match.db
    # Inserts match data -> MatchData.db
    def createMatches(self):
        # Fetch player data
        matches = self.fetchMatches()
        conn, cursor = connect_to_database(MATCH_PATH)
        if matches and conn and cursor:
            try:
                match_data_conn, match_data_cursor = connect_to_database(os.getenv("MATCH_DATA_DIR"))
                if match_data_conn and match_data_cursor:
                    for match_id in matches:
                        # Check if data exists in DB 
                        match_data_cursor.execute("SELECT matchData FROM MatchData WHERE matchId=?", (match_id,))
                        row = match_data_cursor.fetchone()
                        
                        if row:
                            # matchData already in db
                            match_json = json.loads(row[0])
                        else:
                            # Fetch calling API 
                            logging.info(f"Fetching and caching match data from Match ID: {match_id}")
                            try :
                                self.api_service.get_match_data_by_matchId(match_id)
                                match_data_cursor.execute("SELECT matchData FROM MatchData WHERE matchId=?", (match_id,))
                                row = match_data_cursor.fetchone()
                                
                                if not row:
                                    logging.warning(f"Match ID {match_id} not found or not cached")
                                    continue
                                match_json = json.loads(row[0])
                                
                            except Exception as e:
                                logging.warning(f"⚠️ Skipping match ID: {match_id}: {e}")
                                continue
                            
                        if "httpStatus" in match_json and match_json.get("httpStatus") == 404:
                            logging.warning(f"❌ Skipping match ID: {match_id}")
                            continue
                            
                        # Extract game creation data
                        game_creation = match_json["info"]["gameCreation"]
                        dt = convertUnixTimestamp(game_creation)
                        
                        # Insert into match db
                        cursor.execute('''
                            INSERT OR IGNORE INTO Match (matchId, date)
                            VALUES (?, ?)
                            ;
                        ''', (match_id, dt,)
                        )
                        
                    # Commit the transaction
                    conn.commit()
                logging.info(f"✅ Successfully inserted {match_id} into Match table")
            except sqlite3.Error as e:
                logging.error(f"Error inserting data into Match table: {e}")
            finally:
                if match_data_conn:
                    match_data_conn.close()
                conn.close()
        else:
            logging.error("Match data not fetched or database connection failed.")
    
    # Get matches from sqlite db
    def getMatches(self):
        conn, cursor = connect_to_database(os.getenv("MATCHES_DIR"))
        if conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
        if conn is None or cursor is None:
            logging.error("Failed to connect to the database.")
            return []
        try:
            cursor.execute("SELECT * FROM Match")
            rows = cursor.fetchall()
            matches = [dict(row) for row in rows]
            logging.info("Successfully retrieved Match table")
            return matches
        except sqlite3.Error as e:
            logging.error(f"Error getting Matches from Match table: {e}")
            return []