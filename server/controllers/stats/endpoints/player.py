import sqlite3
import logging
import os

from server.config.database import connect_to_database
from server.controllers.stats.endpoints.get_account_by_riot_id import AccountByRiotID
from server.controllers.stats.endpoints.get_active_region import ActiveRegion
from server.controllers.stats.endpoints.get_summoner_by_puuid import Summoner
from server.controllers.stats.endpoints.get_tier_by_id import getTierById

from dotenv import load_dotenv
load_dotenv()

PLAYER_PATH = os.getenv("PLAYER_DIR")

class RiotAPIService:
    def get_account_by_riot_id(self, gameName, tagLine):
        a = AccountByRiotID(gameName, tagLine)
        return a.load_response()

    def get_active_region(self, game, puuid):
        b = ActiveRegion(game, puuid)
        return b.load_response()

    def get_summoner_data(self, puuid):
        c = Summoner(puuid)
        return c.load_response()
    
    def get_tier_by_riot_id(self, puuid):
        d = getTierById(puuid)
        return d.load_response()

class PlayerController:
    def __init__(self, gameName=None, tagLine=None, puuid=None, game="lol"):
        self.gameName = gameName
        self.tagLine = tagLine
        self.puuid = puuid
        self.game = game
        self.profileIconId = 0
        self.summonerLevel = 0
        self.tier = None
        self.api_service = RiotAPIService()

    def fetchPlayerData(self):
        # Step 1: Fetch account data (this gives us the puuid)
        if self.gameName and self.tagLine:
            account_data = self.api_service.get_account_by_riot_id(self.gameName, self.tagLine)
        else:
            print("No gameName or tagLine")
            return None
        
        if isinstance(account_data, dict):
            self.puuid = account_data.get("puuid", None)
            
        if self.puuid:
            # Step 2: Fetch active region and summoner data concurrently using the puuid
            active_region_data = self.api_service.get_active_region(self.game, self.puuid)
            summoner_data = self.api_service.get_summoner_data(self.puuid)
            tier_data = self.api_service.get_tier_by_riot_id(self.puuid)

            # Step 3: Process results
            if isinstance(active_region_data, dict) and isinstance(summoner_data, dict) and isinstance(tier_data, dict):
                self.game = active_region_data.get("region", "")
                self.profileIconId = summoner_data.get("profileIconId", 0)
                self.summonerLevel = summoner_data.get("summonerLevel", 0)
                self.tier = tier_data.get("tier", "")
                return {
                    "puuid": self.puuid,
                    "gameName": self.gameName,
                    "tagLine": self.tagLine,
                    "server": self.game,
                    "profileIconId": self.profileIconId,
                    "summonerLevel": self.summonerLevel,
                    "tier": self.tier
                }
        else:
            print("Error: PUUID not found, cannot fetch active region or summoner data.")
            return None

    def createPlayer(self):
        # Fetch player data
        player_data = self.fetchPlayerData()
        conn, cursor = connect_to_database(PLAYER_PATH)

        if player_data and conn and cursor:
            try:
                # Prepare the data for insertion into the database
                cursor.execute('''
                    INSERT INTO Player (puuid, gameName, tagLine, server, summonerIconId, summonerLevel, tier)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ;
                ''', (
                    player_data["puuid"], 
                    player_data["gameName"], 
                    player_data["tagLine"],
                    player_data["server"],
                    player_data["profileIconId"], 
                    player_data["summonerLevel"],
                    player_data["tier"]
                ))

                # Commit the transaction
                conn.commit()
                logging.info("✅ Successfully inserted data into Player table")
            except sqlite3.Error as e:
                logging.error(f"Error inserting data into Player table: {e}")
            finally:
                conn.close()
        else:
            logging.error("Player data not fetched or database connection failed.")
    
    def getPlayers(self):
        conn, cursor = connect_to_database(os.getenv("PLAYER_DIR"))
        if conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
        if conn is None or cursor is None:
            logging.error("Failed to connect to the database.")
            return []
        try:
            cursor.execute("SELECT * FROM Player")
            rows = cursor.fetchall()
            players = [dict(row) for row in rows]
            logging.info("Successfully retrieved Player table")
            return players
        except sqlite3.Error as e:
            logging.error(f"Error getting Players from Player table: {e}")
            return []
    
    """ ----- Finish implementing ----- """
    async def getPlayerById(self):
        pass
    
    async def deletePlayer(self):
        pass
    
    async def updatePlayer(self):
        pass
    
