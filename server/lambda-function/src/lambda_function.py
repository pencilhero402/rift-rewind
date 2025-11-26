import json
import boto3
import time
from datetime import datetime 
import os
import logging
import urllib.request
import urllib.parse
import mysql.connector
from formatter import format_match_data_by_player, format_aggregate_champion_stats

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# SQS client
sqs = boto3.client('sqs', region_name='us-east-1')

try:
    high_priority_queue_url = sqs.get_queue_url(QueueName='high-priority-queue')['QueueUrl']
    player_queue_url = sqs.get_queue_url(QueueName='player')['QueueUrl']
    match_queue_url = sqs.get_queue_url(QueueName='match')['QueueUrl']
    logger.info(f"SQS High Priority Queue URL: {high_priority_queue_url}")
    logger.info(f"SQS Player Queue URL: {player_queue_url}")
    logger.info(f"SQS Match Queue URL: {match_queue_url}")
except Exception as e:
    logger.exception("Failed to get SQS queue URL")
    high_queue_url = None
    player_queue_url = None
    match_queue_url = None

getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'
healthPath = '/health'
playerPath = '/player'
playersPath = '/players'
playerStatPath = '/player/stat'
playerStatsPath = '/players/stats'
matchPath = '/match'
matchesPath = '/matches'
matchTimelinePath = '/match/timeline'
matchTimelinesPath = '/matches/timelines'

matchHistoryPath = '/match-history'

championStatsPath = '/champion-stats'

# RDS Database Environment Variables
rds_user = os.environ['RDS_USER']
rds_password = os.environ['RDS_PASSWORD']
rds_host = os.environ['RDS_HOST']
rds_port = int(os.environ.get("RDS_PORT", 3306))

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
    logging.info(f"Received event path: {event.get('path')}, HTTP method: {event.get('httpMethod')}")
    logging.info(event)
    httpMethod = event.get('httpMethod')
    path = event.get('path')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    #get_all_aggregate_champion_stats(conn, cursor)
    # Safely parse JSON body if it exists
    try:
        body = event.get('body')
        if body:
            try:
                logger.info(f"Body of request: {body}")
                data = json.loads(body)
                logger.info(f"Body of message: {data}")
            except:
                return buildResponse(400, {"error": "Invalid JSON in request body"})
        else:
            data = {}

        # Routing
        if path == healthPath and httpMethod == getMethod:
            httpResponse = buildResponse(200, "Healthy")

        # Player Routes
        elif path == playerPath:
            if httpMethod == getMethod:
                return get_player(event, conn, cursor)
            if httpMethod == postMethod:
                return handle_player_request(json.loads(event['body']))
            if httpMethod == patchMethod:
                return updatePlayer()
            elif httpMethod == deleteMethod:
                res = delete_player(json.loads(event['body']), conn=conn, cursor=cursor)
                return res
        
        # Players 
        elif path == playersPath and httpMethod == getMethod:
            return get_players(conn, cursor)
        
        # All Players Stats'
        elif path == playerStatsPath:
            if httpMethod == getMethod:
                return get_all_player_stats(conn, cursor)
        
        # Player Stat
        elif path == playerStatPath:
            if httpMethod == getMethod:
                return get_player_stats(event, conn, cursor)
            elif httpMethod == postMethod:
                res = add_player_stats(json.loads(event['body']))
                logger.info(f"Add Player Stats return: {res}")
                return res

        # Match 
        elif path == matchPath:
            if httpMethod == postMethod:
                res = add_match(json.loads(event['body']))
                logging.info(f"Add match ids: {res}")
                return res
            elif httpMethod == getMethod:
                return get_match(event, conn, cursor)

        # All matches
        elif path == matchesPath and httpMethod == getMethod:
            return get_all_matches(conn, cursor)

        # All match data by Player --  /match-history?gameName=melon&tagLine=23333
        elif path == matchHistoryPath and httpMethod == getMethod:
            return get_match_data_by_player(conn, cursor, event)

        # Match timeline
        elif path == matchTimelinePath:
            if httpMethod == getMethod:
                return get_match_timeline(event, conn, cursor)
            elif httpMethod == postMethod:
                res = add_match_timeline(json.loads(event['body']))
                return res
        
        # All match timelines
        elif path == matchTimelinesPath and httpMethod == getMethod:
            return get_all_match_timelines(conn, cursor, event)
        
        # All champion stats 
        elif path == championStatsPath and httpMethod == getMethod:
            return get_all_aggregate_champion_stats(conn, cursor)

        else:
            return buildResponse(404, {"error": "Not found"})

    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON body: {body}")
        return buildResponse(400, {"error": "Invalid JSON in request body"})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_connection():
    return mysql.connector.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        port=rds_port,
        database="rift_rewind",
        charset='utf8mb4',
        use_unicode=True
    )

# ----------- GET requests -----------
def get_player(event, conn, cursor):
    try:
        params = event.get('queryStringParameters') or {}
        gameName = params.get('gameName').encode("utf-8").decode("utf-8")
        tagLine = params.get('tagLine').encode("utf-8").decode("utf-8")

        if not gameName or not tagLine:
            return buildResponse(400, {"error": "Missing gameName or tagLine"})

        query = "SELECT * FROM Player WHERE gameName=%s and tagLine=%s"
        cursor.execute(query, (gameName, tagLine))
        player = cursor.fetchone()

        if not player:
            return buildResponse(404, {"message": "Player not found"})
        return buildResponse(200, player)
    except Exception as e:
        logger.exception("failed to get players from database")
        return buildResponse(500, {"error": str(e)})

def get_player_stats(event, conn, cursor):
    params = event.get('queryStringParameters') or {}
    gameName = params.get('gameName')
    tagLine = params.get('tagLine')
    if not gameName or not tagLine:
        return buildResponse(400, {"error": "Missing gameName or tagLine"})
    try:
        fields_to_parse = ['topChampions', 'role', 'aggression', 'income', 'vision', 'objective']

        cursor.execute(
            """ SELECT * 
                FROM PlayerStats 
                WHERE puuid = (
                    SELECT puuid 
                    FROM Player 
                    WHERE gameName = %s AND tagLine = %s
                )""",
                (gameName, tagLine, )
        )
        res = cursor.fetchone()
        if not res:
            return buildResponse(404, {"message": "Player stats not found"})
        
        for field in fields_to_parse:
            if field in res and res[field]:
                try:
                    res[field] = json.loads(res[field])
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse field '{field}': {e}")
        return buildResponse(200, res)
    except Exception as e:
        logger.exception("failed to get player stats from database")
        return buildResponse(500, {"error": str(e)})

def get_match(event, conn, cursor):
    try:
        params = event.get('queryStringParameters') or {}
        matchId = params.get('matchId')

        if not matchId:
            return buildResponse(400, {"error": "Missing matchId"})

        query = "SELECT * FROM MatchData WHERE matchId=%s"
        cursor.execute(query, (matchId,))
        match = cursor.fetchone()

        if not match:
            return buildResponse(404, {"message": "Match not found"})

        if 'matchData' in match and match['matchData']:
            try:
                match['matchData'] = json.loads(match['matchData'])
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse matchData JSON: {e}")
                # leave as string if parsing fails
        return buildResponse(200, match)
    except Exception as e:
        logger.exception("failed to get matches from database")
        return buildResponse(500, {"error": str(e)})

def get_match_timeline(event, conn, cursor):
    try:
        # Get matchId from query parameters
        params = event.get('queryStringParameters') or {}
        matchId = params.get('matchId')

        if not matchId:
            return buildResponse(400, {"error": "Missing matchId"})

        # Fetch timeline from DB
        query = "SELECT * FROM MatchTimeline WHERE matchId=%s"
        cursor.execute(query, (matchId,))
        row = cursor.fetchone()

        if not row:
            return buildResponse(404, {"message": "Match timeline not found"})

        # Parse JSON if available
        if 'matchTimeline' in row and row['matchTimeline']:
            try:
                row['matchTimeline'] = json.loads(row['matchTimeline'])
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse timeline JSON: {e}")
                # leave as string if parsing fails

        # Return full JSON
        return buildResponse(200, row)

    except Exception as e:
        logger.exception("Failed to get match timelines from database")
        return buildResponse(500, {"error": str(e)})

def get_match_data_by_player(conn, cursor, event):
    try:
        # Extract query parameters safely
        params = event.get('queryStringParameters', {})
        gameName = params.get('gameName')
        tagLine = params.get('tagLine')

        if not gameName or not tagLine:
            logger.error("Missing gameName or tagLine")
            return buildResponse(400, {"error": "Missing gameName or tagLine"})

        query = """ SELECT 
                        md.matchId,
                        CAST(JSON_UNQUOTE(JSON_EXTRACT(md.matchData, '$.info.gameStartTimestamp')) AS UNSIGNED) AS gameStartTimestamp,
                        CAST(JSON_UNQUOTE(JSON_EXTRACT(md.matchData, '$.info.gameDuration')) AS UNSIGNED) AS gameDuration,
                        GROUP_CONCAT(pt.summonerName) AS summonerNames,
                        GROUP_CONCAT(pt.championName) AS championNames,
                        GROUP_CONCAT(CAST(pt.win AS UNSIGNED)) AS outcomes,
                        GROUP_CONCAT(pt.lane) AS lanes,
                        GROUP_CONCAT(pt.role) AS roles,
                        GROUP_CONCAT(pt.summoner1Id) AS summonerSpells1,
                        GROUP_CONCAT(pt.summoner2Id) AS summonerSpells2,
                        JSON_ARRAYAGG(JSON_EXTRACT(pt.perks, '$.styles[0].style')) AS primaryStyles,
                        JSON_ARRAYAGG(JSON_EXTRACT(pt.perks, '$.styles[0].selections[0].perk')) AS primaryKeystones,
                        JSON_ARRAYAGG(JSON_EXTRACT(pt.perks, '$.styles[1].style')) AS secondaryStyles,

                        GROUP_CONCAT(pt.kills) AS kills,
                        GROUP_CONCAT(pt.deaths) AS deaths,
                        GROUP_CONCAT(pt.assists) AS assists,
                        GROUP_CONCAT(pt.kda) AS kda,

                        GROUP_CONCAT(pt.item0) AS item0,
                        GROUP_CONCAT(pt.item1) AS item1,
                        GROUP_CONCAT(pt.item2) AS item2,
                        GROUP_CONCAT(pt.item3) AS item3,
                        GROUP_CONCAT(pt.item4) AS item4,
                        GROUP_CONCAT(pt.item5) AS item5,
                        GROUP_CONCAT(pt.item6) AS item6,

                        GROUP_CONCAT(pt.teamId) AS teamIds

                    FROM MatchData md
                    JOIN JSON_TABLE(
                        md.matchData, 
                        '$.info.participants[*]' COLUMNS (
                            puuid VARCHAR(255) PATH '$.puuid',
                            summonerName VARCHAR(255) PATH '$.riotIdGameName',
                            riotIdTagline VARCHAR(10) PATH '$.riotIdTagline',
                            win BOOLEAN PATH '$.win',
                            championName VARCHAR(100) PATH '$.championName',
                            lane VARCHAR(20) PATH '$.lane',
                            role VARCHAR(20) PATH '$.role',
                            summoner1Id INT PATH '$.summoner1Id',
                            summoner2Id INT PATH '$.summoner2Id',
                            perks JSON PATH '$.perks',
                            kills INT PATH '$.kills',
                            deaths INT PATH '$.deaths',
                            assists INT PATH '$.assists',
                            kda FLOAT PATH '$.challenges.kda',
                            item0 INT PATH '$.item0',
                            item1 INT PATH '$.item1',
                            item2 INT PATH '$.item2',
                            item3 INT PATH '$.item3',
                            item4 INT PATH '$.item4',
                            item5 INT PATH '$.item5',
                            item6 INT PATH '$.item6',
                            teamId INT PATH '$.teamId'
                        )
                    ) AS pt
                    WHERE md.matchId IN (
                        SELECT md2.matchId
                        FROM MatchData md2
                        JOIN JSON_TABLE(
                            md2.matchData,
                            '$.info.participants[*]' COLUMNS (
                                summonerName VARCHAR(255) PATH '$.riotIdGameName',
                                riotIdTagline VARCHAR(10) PATH '$.riotIdTagline'
                            )
                        ) AS p
                        WHERE p.summonerName = %s AND p.riotIdTagline = %s
                    )
                    GROUP BY md.matchId, gameStartTimestamp, gameDuration;
            """
        cursor.execute(query, (gameName, tagLine))
        rows = cursor.fetchall()  

        # Transform data to be more readable
        if rows:
            logger.info(f"{len(rows)} matches retrieved for {gameName}#{tagLine}")
            columns = [col[0] for col in cursor.description]
            logger.info(f"First row: {rows[0]}")
            result = format_match_data_by_player(rows, columns)
            return buildResponse(200, result)
        else:
            logger.info(f"No match data found for {gameName}#{tagLine}")
            return buildResponse(200, [])

    except Exception as e:
        logger.exception(f"Failed to get match data from database for {gameName}#{tagLine}")
        return buildResponse(500, {"error": str(e)})

def get_players(conn, cursor):
    try:
        cursor.execute("SELECT * FROM Player")
        players = cursor.fetchall()
        return buildResponse(200, players)
    except Exception as e:
        logger.exception("failed to get players from database")
        return buildResponse(500, {"error": str(e)})

def get_all_player_stats(conn, cursor):
    try:
        cursor.execute("SELECT * FROM PlayerStats")
        player_stats = cursor.fetchall()
        json_fields = ['topChampions', 'role', 'aggression', 'income', 'vision', 'objective']

        for record in player_stats:
            for field in json_fields:
                if field in record and record[field]:
                    try:
                        record[field] = json.loads(record[field])
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse field '{field}' in player {record.get('puuid')}: {e}")
        return buildResponse(200, player_stats)
    except Exception as e:
        logger.exception("failed to get player stats from database")
        return buildResponse(500, {"error": str(e)})

def get_all_matches(conn, cursor):
    """ Returns all matchIds from MatchData
    """
    try:
        cursor.execute("SELECT matchId FROM MatchData;")
        matches = cursor.fetchall()
        return buildResponse(200, matches)
    except Exception as e:
        logger.exception("failed to get matches from database")
        return buildResponse(500, {"error": str(e)})

def get_all_match_timelines(conn, cursor):
    """ Returns all matchIds from MatchTimeline
    """
    try:
        cursor.execute("SELECT matchId FROM MatchTimeline;")
        match_timelines = cursor.fetchall()
        return buildResponse(200, match_timelines)
    except Exception as e:
        logger.exception("failed to get match timelines from database")
        return buildResponse(500, {"error": str(e)})

def get_all_aggregate_champion_stats(conn, cursor):
    """Returns all aggregate champion stats"""
    try:
        cursor.execute("SELECT * FROM AggregateChampionStats;")
        rows = cursor.fetchall()
        # Transform data to be more readable
        if rows:
            logger.info(f"{len(rows)} champions retrieved.")
            columns = [col[0] for col in cursor.description]
            logger.info(f"First row: {rows[0]}")
            result = format_aggregate_champion_stats(rows, columns)
            return buildResponse(200, result)
        else:
            logger.info(f"No match data found for {gameName}#{tagLine}")
            return buildResponse(200, [])
        return buildResponse(200, rows)

    except Exception as e:
        logger.exception("Failed to get aggregate champion stats from database")
        return buildResponse(500, {"error": str(e)})

# ----------- Send POST message -----------
def add_player(requestBody):
    if not player_queue_url:
        logger.error("SQS queue URL not configured or unavailable")
        return buildResponse(500, {"error": "Internal server error. SQS queue not available."})

    if not requestBody or "gameName" not in requestBody or "tagLine" not in requestBody:
        return buildResponse(400, {"error": "Missing gameName or tagLine"})

    gameName = requestBody["gameName"]
    tagLine = requestBody["tagLine"]
    
    if not gameName or not tagLine:
        return buildResponse(400, {"error": "Missing gameName or tagLine"})

    try:
        message = {
            "action": "create",
            "data": {
                "gameName": gameName,
                "tagLine": tagLine
            }
        }
        sqs.send_message(
            QueueUrl=player_queue_url,
            MessageBody=json.dumps(message)
        )
        logger.info("Message send to SQS successfully")
        logger.info(f"SQS Message Sent: {message}")
        return buildResponse(200, {"message": f"Player added successfully {gameName}#{tagLine}"})
    except Exception as e:
        logger.exception("failed to send message to SQS")
        return buildResponse(500, {"error": "Failed to enqueue player data", "details": str(e)})

def add_player_stats(requestBody):
    if not player_queue_url:
        logger.error("SQS queue URL not configured or unavailable")
        return buildResponse(500, {"error": "Internal server error. SQS queue not available."})
    logger.info(f"add_player_stats requestBody: {requestBody}")

    if not requestBody or "puuid" not in requestBody:
        return buildResponse(400, {"error": "Missing puuid"})

    try:
        message = {
            "action": "create_player_stats",
            "data": requestBody
        }
        sqs.send_message(
            QueueUrl=player_queue_url,
            MessageBody=json.dumps(message)
        )
        logger.info("Message send to SQS successfully")
        logger.info(f"SQS Message Sent: {message}")
        return buildResponse(200, {"message": f"Sent message to add player stats {requestBody}"})
    except Exception as e:
        logger.exception("failed to send message to SQS")
        return buildResponse(500, {"error": "Failed to enqueue player data", "details": str(e)})

def delete_player(event, conn, cursor):
    try:
        params = event.get('queryStringParameters') or {}
        gameName = params.get('gameName')
        tagLine = params.get('tagLine')

        if not gameName or not tagLine:
            return buildResponse(400, {"error": "Missing gameName or tagLine"})

        cursor.execute("DELETE FROM Player WHERE gameName=%s and tagLine=%s", (gameName, tagLine))
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"Successfully deleted {gameName}#{tagLine} from Player table")
        return buildResponse(200, {"message": f"Successfully deleted {deleted_count}"})
    except Exception as e:
        logger.exception("failed to get player stats from database")
        return buildResponse(500, {"error": str(e)})

def add_match_data_with_match_ids(match_ids):
    if not match_queue_url:
        logger.error("SQS queue URL not configured or unavailable")
        return buildResponse(500, {"error": "SQS queue not available"})
    
    if not match_ids:
        return buildResponse(400, {"error": "Missing matchIds"})
    
    try:
        # split match_ids into chunks of 10
        for i in range(0, len(match_ids), 10):
            batch = match_ids[i:i+10]
            entries = [
                {"Id": str(idx), "MessageBody": json.dumps({"action": "create_match_data", "data": {"match_id": m}})}
                for idx, m in enumerate(batch)
            ]
            sqs.send_message_batch(QueueUrl=match_queue_url, Entries=entries)

        logger.info(f"SQS messages sent for match IDs: {match_ids}")
        return buildResponse(200, {"message": f"Matches added successfully: {match_ids}"})
    except Exception as e:
        logger.exception("Failed to send messages to SQS")
        return buildResponse(500, {"error": f"Failed to enqueue match ids: {str(e)}"})

def add_match_with_puuid(requestBody):
    if not match_queue_url:
        logger.error("SQS queue URL not configured or unavailable")
        return buildResponse(500, {"error": "Internal server error. SQS queue not available."})

    if not requestBody or "puuid" not in requestBody:
        return buildResponse(400, {"error": "Missing puuid"})

    puuid = requestBody["puuid"]

    match_ids = fetch_match_ids(puuid=puuid)
    
    if not match_ids:
        logger.warning("No match ids: found for provided Riot ID.")
        return buildResponse(404, {"error": "No Clash Matches found for Riot Id"})

    try:
        for match_id in match_ids:
            match_data = fetch_match_data(match_id)

            message = {
                "action": "create",
                "data": {
                    "match_id": match_id,
                    "match_data": match_data
                    }
            }
            sqs.send_message(
                QueueUrl=match_queue_url,
                MessageBody=json.dumps(message)
            )
            logger.info("Message send to SQS successfully")
            logger.info(f"SQS Message Sent: {message}")
        return buildResponse(200, {"message":  f"Matches added successfully: {match_ids}"})
    except Exception as e:
        logger.exception("failed to send message to SQS")
        return buildResponse(500, {"error": f"Failed to enqueue match ids:: {str(e)}"})

def add_match_timeline_with_match_ids(match_ids):
    if not match_queue_url:
        logger.error("SQS queue URL not configured or unavailable")
        return buildResponse(500, {"error": "Internal server error. SQS queue not available."})

    if not match_ids:
        return buildResponse(400, {"error": "Missing matchIds"})

    successful = []
    failed = []

    for match_id in match_ids:
        try:
            message = {
                "action": "create_match_timeline",
                "data": {
                    "match_id": match_id,
                }
            }

            sqs.send_message(
                QueueUrl=match_queue_url,
                MessageBody=json.dumps(message)
            )
            logger.info(f"SQS message sent for match timeline: {match_id}")
            successful.append(match_id)

        except Exception as e:
            logger.exception(f"Failed to enqueue match timeline for {match_id}")
            failed.append(match_id)

    return buildResponse(200, {
        "message": "Match timelines processed",
        "successful": successful,
        "failed": failed
    })

def add_match_timeline(requestBody):
    if not match_queue_url:
        logger.error("SQS queue URL not configured or unavailable")
        return buildResponse(500, {"error": "Internal server error. SQS queue not available."})

    if not requestBody or "matchId" not in requestBody:
        return buildResponse(400, {"error": "Missing matchId"})

    matchId = requestBody["matchId"]

    try:
        if not match_timeline:
            logger.warning("No match timeline found for provided matchId.")
            return buildResponse(404, {"error": "Match timeline not found"})

        message = {
            "action": "create_match_timeline",
            "data": {
                "match_id": matchId,
            }
        }
        sqs.send_message(
            QueueUrl=match_queue_url,
            MessageBody=json.dumps(message)
        )
        logger.info("Message sent to SQS successfully")
        logger.info(f"SQS Message Sent: {message}")
        return buildResponse(200, {"message": f"Match timeline added successfully: {matchId}"})
    except Exception as e:
        logger.exception("Failed to send message to SQS")
        return buildResponse(500, {"error": f"Failed to enqueue match timeline: {str(e)}"})

def add_all_aggregate_champion_stats():
    if not match_queue_url:
        logger.error("SQS queue URL not configured or unavailable")
        return buildResponse(500, {"error": "Internal server error. SQS queue not available."})

    try:
        message = {
            "action": "create_all_aggregate_champion_stats",
            "data": {}
        }
        sqs.send_message(
            QueueUrl=match_queue_url,
            MessageBody=json.dumps(message)
        )
        logger.info("Message sent to SQS successfully")
        logger.info(f"SQS Message Sent: {message}")
        return buildResponse(200, {"message": "Aggregate champion stats added successfully"})
    except Exception as e:
        logger.exception("Failed to send message to SQS")
        return buildResponse(500, {"error": f"Failed to enqueue aggregate champion stats: {str(e)}"})


# ----- RIOT API CALLS ----- 
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

def fetch_match_ids(puuid, startTime=None, endTime=None, queue=700, type_=None, start=0, count=100):
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

# ----- SEND EVERYTHING ---- 
def handle_player_request(requestBody):
    try:
        gameName = requestBody.get("gameName")
        tagLine = requestBody.get("tagLine")
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        return buildResponse(400, {"error": "Failed to parse request body"})

    if not gameName or not tagLine:
        logger.error("Missing gameName or tagLine")
        return {"error": "Missing gameName or tagLine"}

    # 1️⃣ Send Player Data
    player_data = fetch_riot_account(gameName, tagLine)
    if not player_data:
        logger.error(f"No player data found for {gameName}#{tagLine}")
        return buildResponse(404, {"error": "Player not found"})
    
    add_player({"gameName": gameName, "tagLine": tagLine})

    puuid = player_data.get("puuid")

    if not puuid:
        logger.error(f"Unable to retrieve puuid for {gameName}#{tagLine}")
        return {"error": "Failed to fetch player data"}

    # 2️⃣ Send Match IDs
    match_ids = fetch_match_ids(puuid)

    if not match_ids:
        logger.error(f"Unable to retrieve match ids for {gameName}#{tagLine}")
        return {"error": "Failed to fetch match ids"}

    # 3️⃣ Send PlayerMatchHistory & MatchData & MatchTimeline
    match_data = add_match_data_with_match_ids(match_ids)   # Upsert matchData
    match_timeline_data = add_match_timeline_with_match_ids(match_ids) # Upsert matchTimeline

    # 4️⃣ Send AggregateChampionStats
    all_champion_stats_data = add_all_aggregate_champion_stats()

    if not match_data or not match_timeline_data:
        logger.error(f"Failed to add match data or match timeline data for {gameName}#{tagLine}")
        return {"error": "Failed to add match data or match timeline data"}

    # 4️⃣ Send PlayerStats
    player_stats = add_player_stats(player_data)    # Upsert PlayerStats
    result = {
        "player_data": player_data,
        "match_data": match_data,
        "match_timeline_data": match_timeline_data,
        "player_stats": player_stats
    }

    logger.info(f"Successfully processed player request for {gameName}#{tagLine}")
    return result

def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body)
    return response