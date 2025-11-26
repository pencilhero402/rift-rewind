import json
import os
import logging
from datetime import datetime
import mysql.connector
import urllib.request
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# RDS configuration
rds_user = os.environ['RDS_USER']
rds_password = os.environ['RDS_PASSWORD']
rds_host = os.environ['RDS_HOST']
rds_port = int(os.environ.get('RDS_PORT', 3306))
rds_db = os.environ.get('RDS_DB', 'rift_rewind')

STATS_HEADERS = {
    "X-Riot-Token": os.environ.get("RIOT_API_KEY"),
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com"
}

# Warm lambda connection
conn = None
cursor = None

def lambda_handler(event, context):
    """
    This Lambda is triggered by SQS. event['Records'] contains SQS messages.
    """
    # Connect to database once
    conn = get_connection()
    cursor = conn.cursor()

    for record in event['Records']:
        logger.info(f"Type of record['body']: {type(record['body'])}")
        logger.info(f"Content of record['body']: {record['body']}")
        try:
            # Check if the body is a string. If it's already a dictionary, no need to load it.
            if isinstance(record['body'], str):
                try:
                    message = json.loads(record['body'])  # Deserialize string to Python dict
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON from body: {record['body']}")
                    raise ValueError("Invalid JSON in body")
            else:
                message = record['body']  # If it's already a dictionary, use it directly

            logging.info(f"Processing message: {message}")

            # Extract action and data from the message
            action = message.get('action')
            data = message.get('data')
            logging.info(f"Type of data {type(data)}")
            logging.info(f"Data stored in message: {data}")
            if isinstance(data, str):
                data = json.loads(data)

            if isinstance(data, dict):
                data_item = data
            
            logger.info(f"Action: {action}, data: {data}")

            # Handle different actions based on the message
            if action == 'create_match_data':
                match_id = data_item['match_id']
                upsert_match_data(match_id, conn, cursor)
            elif action == 'create_match_timeline':
                match_id = data_item['match_id']
                upsert_match_timeline(match_id, conn, cursor)
            elif action == 'create_all_aggregate_champion_stats':
                upsert_all_aggregate_champion_stats(conn, cursor)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except Exception as e:
            # Log and handle any errors that occur during message processing
            logger.exception(f"Failed to process message: {record['body']}")

    if cursor:
        cursor.close()
    if conn:
        conn.close()

    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }

def get_connection():
    return mysql.connector.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        port=rds_port,
        database=rds_db
    )

def upsert_match_data(match_id, conn, cursor):
    try:
        # Check if match data already exists
        cursor.execute("SELECT * FROM MatchData WHERE matchId = %s", (match_id,))
        existing_match = cursor.fetchone()
        if existing_match:
            logger.info(f"Match data already exists for matchID: {match_id}")
            return
        
        match_data = json.dumps(fetch_match_data(match_id))
        cursor.execute(
            """ INSERT IGNORE INTO MatchData( matchId, matchData )
                VALUES (%s, %s)
            """,
            (match_id, match_data)
            )
        conn.commit()
        match = cursor.fetchone()
        logger.info(f"✅ Inserted matchID: {match_id} into MatchData table!")
        return match
    except Exception as e:
        logger.exception(f"Failed to insert match data: {match_id}")

def upsert_match_timeline(match_id, conn, cursor):
    try:
        match_timeline_data = json.dumps(fetch_match_timeline_data(match_id))
        cursor.execute(
            """ INSERT IGNORE INTO MatchTimeline(matchId, matchTimeline)
                VALUES (%s, %s)
            """,
            (match_id, match_timeline_data)
        )
        conn.commit()
        match_timeline = cursor.fetchone()
        logger.info(f"✅ Inserted matchID: {match_id} into MatchTimeline table!")
        return match_timeline
    except Exception as e:
        logger.exception(f"Failed to insert match timeline: {match_id}")

def upsert_all_aggregate_champion_stats(conn, cursor):
    """ Returns aggregate stats for all champions
    """
    try:
        cursor.execute("""
            INSERT INTO AggregateChampionStats (
                champion_id,
                champion_name,
                kp,
                dpm,
                solo_kills,
                dmg_percent,
                gpm,
                cspm,
                gold_percentage,
                avg_vpm,
                avg_vision_score,
                avg_wards_cleared,
                avg_dmg_to_turrets,
                avg_turret_takedowns,
                games_played
            )
            SELECT
                p.championKey AS champion_id,
                p.championName AS champion_name,
                AVG(p.kp) AS kp,
                AVG(p.dpm) AS dpm,
                AVG(p.soloKills) AS solo_kills,
                AVG(p.dmgPercent) AS dmg_percent,
                AVG(p.gpm) AS gpm,
                AVG((p.total_cs + p.neutral_cs) / (j.gameDuration / 60)) AS cspm,
                AVG(p.player_gold / t.team_gold) AS gold_percentage,
                AVG(p.vpm) AS avg_vpm,
                AVG(p.visionScore) AS avg_vision_score,
                AVG(p.wardsCleared) AS avg_wards_cleared,
                AVG(p.damageToTurrets) AS avg_dmg_to_turrets,
                AVG(p.turretTakedowns) AS avg_turret_takedowns,
                COUNT(*) AS games_played
            FROM MatchData m
            -- extract participant stats
            JOIN JSON_TABLE(
                m.matchData,
                '$.info.participants[*]'
                COLUMNS (
                    championName        VARCHAR(100) PATH '$.championName',
                    championKey         VARCHAR(10)  PATH '$.championId',

                    kp                  DOUBLE PATH '$.challenges.killParticipation',
                    dpm                 DOUBLE PATH '$.challenges.damagePerMinute',
                    soloKills           DOUBLE PATH '$.challenges.soloKills',
                    dmgPercent          DOUBLE PATH '$.challenges.teamDamagePercentage',

                    gpm                 DOUBLE PATH '$.challenges.goldPerMinute',

                    vpm                 DOUBLE PATH '$.challenges.visionScorePerMinute',
                    visionScore         DOUBLE PATH '$.visionScore',
                    wardsCleared        DOUBLE PATH '$.wardsKilled',

                    damageToTurrets     DOUBLE PATH '$.damageDealtToTurrets',
                    turretTakedowns     DOUBLE PATH '$.turretTakedowns',

                    total_cs            INT PATH '$.totalMinionsKilled',
                    neutral_cs          INT PATH '$.neutralMinionsKilled',

                    puuid               VARCHAR(100) PATH '$.puuid',
                    player_gold         DOUBLE PATH '$.goldEarned',
                    teamId              INT PATH '$.teamId'
                )
            ) AS p
            -- extract game duration
            JOIN JSON_TABLE(
                m.matchData,
                '$.info'
                COLUMNS (
                    gameDuration DOUBLE PATH '$.gameDuration'
                )
            ) AS j
            -- compute total team gold per match
            JOIN (
                SELECT 
                    m2.matchId,
                    p3.teamId,
                    SUM(p3.gold) AS team_gold
                FROM MatchData m2
                JOIN JSON_TABLE(
                    m2.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        gold DOUBLE PATH '$.goldEarned',
                        teamId INT PATH '$.teamId'
                    )
                ) AS p3
                GROUP BY m2.matchId, p3.teamId
            ) AS t ON t.matchId = m.matchId AND t.teamId = p.teamId
            GROUP BY p.championKey, p.championName
            ON DUPLICATE KEY UPDATE
                champion_name        = VALUES(champion_name),
                kp                   = VALUES(kp),
                dpm                  = VALUES(dpm),
                solo_kills           = VALUES(solo_kills),
                dmg_percent          = VALUES(dmg_percent),
                gpm                  = VALUES(gpm),
                cspm                 = VALUES(cspm),
                gold_percentage      = VALUES(gold_percentage),
                avg_vpm              = VALUES(avg_vpm),
                avg_vision_score     = VALUES(avg_vision_score),
                avg_wards_cleared    = VALUES(avg_wards_cleared),
                avg_dmg_to_turrets   = VALUES(avg_dmg_to_turrets),
                avg_turret_takedowns = VALUES(avg_turret_takedowns),
                games_played         = VALUES(games_played),
                last_updated         = CURRENT_TIMESTAMP;
            """)
        conn.commit()
        logger.info(f"✅ Inserted all champion stats into AggregateChampionStats Table")
    except Exception as e:
        logger.exception("failed to get champion stats from database")
        return buildResponse(500, {"error": str(e)})

""" ----- RIOT API CALLS ----- """
# Player Calls 
def fetch_riot_account(gameName, tagLine, region="na1"):
    gameName = urllib.parse.quote(gameName)
    tagLine = urllib.parse.quote(tagLine)
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    req = urllib.request.Request(url)
    
    # Add headers
    for k,v in STATS_HEADERS.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data_bytes = response.read()
            data = json.loads(data_bytes.decode('utf-8'))
            return {
                "puuid": data.get("puuid"),
                "gameName": data.get("gameName"),
                "tagLine": data.get("tagLine")
            }       
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")

    return None

def fetch_active_region(puuid, game="lol"):
    url = f"https://americas.api.riotgames.com/riot/account/v1/region/by-game/{game}/by-puuid/{puuid}"
    req = urllib.request.Request(url)

    # Add headers
    for k,v in STATS_HEADERS.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data_bytes = response.read()
            data = json.loads(data_bytes.decode('utf-8'))
            return {
                "region": data.get("region")
            }
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")

    return None

def fetch_summoner_data(puuid):
    url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    req = urllib.request.Request(url)

    # Add headers
    for k,v in STATS_HEADERS.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data_bytes = response.read()
            data = json.loads(data_bytes.decode('utf-8'))
            return {
                "profileIconId": data.get("profileIconId"),
                "summonerLevel": data.get("summonerLevel"),
            }
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")

    return None

def fetch_player_tier(puuid):
    url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
    req = urllib.request.Request(url)
    # Add headers
    for k,v in STATS_HEADERS.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data_bytes = response.read()
            data = json.loads(data_bytes.decode('utf-8'))
            
            # Finds RANKED SOLO/DUO tier
            solo_entry = next((entry for entry in data if entry["queueType"] == "RANKED_SOLO_5x5"), None)
            if solo_entry:
                return {"tier": solo_entry.get("tier"), "rank": solo_entry.get("rank")}
            else:
                return {"tier": None, "rank": None}
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")

    return None

def fetch_all_player_data(gameName, tagLine):
    account_info = fetch_riot_account(gameName, tagLine)
    if not account_info:
        logging.error("Failed to fetch Riot Account")
        return None
    puuid = account_info.get("puuid")
    if not puuid:
        logging.error(f"Failed to retrieve puuid for {gameName}#{tagLine}")

     # Fetch Active Region Data
    active_region_data = fetch_active_region(puuid) or {}
    region = active_region_data.get("region", "na1")  # Default to 'na1' if no region is found

    # Fetch Summoner Data
    summoner_data = fetch_summoner_data(puuid) or {}

    # Fetch Player Tier Data
    player_tier = fetch_player_tier(puuid) or {}

    # Merge all info into single player_data dict
    player_data = {
        "puuid": puuid,
        "gameName": gameName,
        "tagLine": tagLine,
        "region": region,
        "summonerIconId": summoner_data.get("profileIconId"),
        "summonerLevel": summoner_data.get("summonerLevel"),
        "tier": player_tier.get("tier") if player_tier else "UNRANKED"
    }
    return player_data

# Match Calls
def fetch_match_ids(puuid, startTime=None, endTime=None, queue=700, type_=None, start=0, count=5):
    base_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids'
    params = {
        'queue': queue,
        'start': start,
        'count': count
    }

    if startTime is not None:
        params["startTime"] = int(startTime)
    if endTime is not None:
        params["endTime"] = int(endTime)
    if type_ is not None:
        params["type"] = type_
    
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    logging.info(url)
    req = urllib.request.Request(url)

    # Add headers
    for k,v in STATS_HEADERS.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data_bytes = response.read()
            match_ids = json.loads(data_bytes.decode('utf-8'))
            logging.info(f"Found match ids:: {match_ids}")
            return match_ids
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")

    return None

def fetch_match_data(matchId):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{matchId}"
    req = urllib.request.Request(url)

    # Add headers
    for k,v in STATS_HEADERS.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")

    return None

def fetch_match_timeline_data(matchId):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{matchId}/timeline"
    req = urllib.request.Request(url)

    # Add headers
    for k,v in STATS_HEADERS.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")

    return None
