import json
import os
import logging
import time
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

    # Connect to database
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    upsert_player(conn, cursor, {'gameName': 'DBreezy', 'tagLine': 'NA1'})
    
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
                    continue
            else:
                message = record['body']  # If it's already a dictionary, use it directly

            logging.info(f"Processing message: {message}")

            # Extract action and data from the message
            action = message.get('action')
            data = message.get('data')
            player_id = data.get('puuid')

            logger.info(f"Action: {action}, data: {data}, player_id: {player_id}")

            # Handle different actions based on the message
            if action == 'create':
                upsert_player(conn, cursor, data)
            elif action == 'delete':
                delete_player(player_id, conn, cursor)
            elif action == 'create_player_stats':
                upsert_player_stats(conn, cursor, player_id)
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
        database=rds_db,
        charset='utf8mb4',
        use_unicode=True
    )

def upsert_player(conn, cursor, data):
    try:
        player_data = fetch_all_player_data(gameName=data['gameName'], tagLine=data['tagLine'])
        if not player_data:
            logger.error(f"No player data found for {data['gameName']}#{data['tagLine']}")
            return None  # or raise an exception if you prefer
        cursor.execute(
            """ INSERT INTO Player (puuid, gameName, tagLine, region, summonerIconId, summonerLevel, tier ) 
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    gameName=VALUES(gameName),
                    tagLine=VALUES(tagLine),
                    region=VALUES(region),
                    summonerIconId=VALUES(summonerIconId),
                    summonerLevel=VALUES(summonerLevel),
                    tier=VALUES(tier)
            """,
            (player_data['puuid'], data['gameName'], data['tagLine'], player_data['region'], player_data['summonerIconId'], player_data['summonerLevel'], player_data['tier'])
        )
        conn.commit()
        logger.info(f"✅ Upserted player: {data['gameName']}#{data['tagLine']} into Player table!")
        return player_data['puuid']
    except Exception as e:
        logger.exception(f"Failed to insert player: {data['gameName']}")

def delete_player(conn, cursor, player_id):
    try:
        cursor.execute("DELETE FROM Player WHERE puuid=%s", (player_id,))
        conn.commit()
        if cursor.rowcount:
            logger.info(f"Deleted player with puuid: {player_id}")
        else:
            logger.warning(f"No player found with puuid: {player_id}")
    except Exception as e:
        logger.exception(f"Failed to delete player with puuid: {player_id}")

""" ----- PLAYER STAT ----- """
def get_player_matchIds_by_puuid(conn, cursor, puuid):
    """ Returns list of matchIds for player
        Params: puuid: str
        Return: [matchId1, matchId2, ...]
    """
    try:
        cursor.execute(
            """SELECT md.matchId
                FROM MatchData AS md
                JOIN JSON_TABLE(
                    md.matchData,
                    '$.metadata.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$'
                    )
                ) AS jt
                WHERE jt.puuid = %s;
                """, (puuid, ))
        rows = cursor.fetchall()
        logging.info(f"Player matches {rows}")
        logging.info(f"Type of data stored in A ROW: {type(rows[0]['matchId'])}")
        return [row['matchId'] for row in rows]
    except:
        logger.exception(f"Failed to get matches for Player: {puuid}")
        return []

def calculate_role_stats(conn, cursor, puuid):
    """ Returns role stats for player
        Params: puuid: str
        Return: {TOP: 5, BOTTOM: 3, ...} : dict
    """
    try:
        start = time.time()
        cursor.execute(
            """SELECT 
                    p.lane,
                    p.role,
                    COUNT(*) AS times_played
               FROM MatchData m
               JOIN JSON_TABLE(
                   m.matchData,
                   "$.info.participants[*]"
                   COLUMNS (
                       puuid VARCHAR(100) PATH "$.puuid",
                       lane  VARCHAR(50)  PATH "$.lane",
                       role  VARCHAR(50)  PATH "$.role"
                   )
               ) AS p
               WHERE p.puuid = %s
               GROUP BY p.lane, p.role
               ORDER BY times_played DESC;
            """,
            (puuid,)
        )
        rows = cursor.fetchall()
        end = time.time()
        logging.info(f"One Step Query: Total time for queries: {end - start:.4f} seconds")

        if not rows:
            return {}

        # Aggregate lane → role stats
        res = {}
        for row in rows:
            lane = row['lane']
            role = row['role']
            count = row['times_played']

            if lane == "BOTTOM":
                # classify as SUPPORT or BOTTOM
                key = role if role in ["SUPPORT", "CARRY"] else "OTHER_BOTTOM"
                if key == "CARRY":
                    key = "BOTTOM"
            else:
                key = lane

            res[key] = res.get(key, 0) + count

        logging.info(f"Player role stats: {res}")
        return res

    except Exception:
        logger.exception(f"Failed to get role stats for Player: {puuid}")
        return {}

def calculate_primary_role(conn, cursor, puuid):
    """ Return primary/secondary role of player
        Params: puuid: str
        Return: [TOP] or [TOP, BOTTOM] : list
        1) 70%+ on one role -> return [PRIMARY]
        2) 50%+ on PRIMARY/SECONDARY -> return [PRIMARY, SECONDARY]
        3) [FLEX]
    """
    times_on_role = calculate_role_stats(conn, cursor, puuid)
    logger.info(f"Times on role: {times_on_role}")
    if times_on_role == {}:
        return {"Primary": "FLEX"}

    total_games = sum(times_on_role.values())
    logger.info(f"Total games: {total_games}")

    roles = list(times_on_role.keys())
    primary = roles[0]
    secondary = roles[1] if len(roles) > 1 else None

    if times_on_role[primary] / total_games >= 0.7:
        return {"Primary": primary}
    elif secondary and (times_on_role[primary] + times_on_role[secondary]) / total_games >= 0.5:
        return {"Primary": primary, "Secondary": secondary}
    else:
        return {"Primary": "FLEX"}

def get_champions_played(conn, cursor, puuid):
    """ Return most played champion by player
        Params: puuid: str
        Returns: "TRUNDLE": str
    """
    try:
        cursor.execute(
            """ SELECT 
                    p.championName, 
                    COUNT(*) AS times_played
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]' 
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        championName VARCHAR(100) PATH '$.championName'
                    )
                ) AS p
                WHERE p.puuid = %s
                GROUP BY p.championName
                ORDER BY times_played DESC;
        """, (puuid,) )
        champions_played = cursor.fetchall()
        logger.info(f"Champions played: {champions_played}")
        return champions_played
    except:
        logger.exception(f"Failed to calculate most played champion for Player id: {puuid}")

def calculate_most_played_champions(conn, cursor, puuid, number_of_champions=6):
    """ Return most played champions by player in descending order
        Params: puuid: str
        Returns: {"Trundle": 12, "Ahri": 10, ...}
    """
    champions_played = get_champions_played(conn, cursor, puuid)  # already sorted

    # Adjust number_of_champions if fewer champions are available
    number_of_champions = min(number_of_champions, len(champions_played))

    # Take top N and convert to dict
    top_champions = {champion['championName']: champion['times_played'] for champion in champions_played[:number_of_champions]}

    logger.info(f"The top {number_of_champions} champions are: {top_champions}")
    return top_champions

def calculate_player_winrate(conn, cursor, puuid):
    try:
        cursor.execute(
            """ SELECT
                    p.win,
                    COUNT(*) AS times_played
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        win BOOLEAN PATH '$.win'
                    )
                ) AS p
                WHERE p.puuid = %s
                GROUP BY p.win
                ORDER BY times_played DESC;
        """, (puuid,) )
        games = cursor.fetchall()
        logger.info(f"Cursor return: {games}")
        total_games = sum([row['times_played'] for row in games])
        win_percentage = games[0]['times_played'] / total_games
        return win_percentage
    except:
        logger.exception(f"Failed to calculate player winrate for puuid: {puuid}")

def player_damage_per_min(conn, cursor, puuid):
    """ Returns player's damage_per_min
        Params: puuid: str
        Return: damage/min : float
    """
    # '$.info.participants[*].challenges'
    try:    
        cursor.execute(
            """ SELECT AVG(p.damagePerMin) AS avg_dpm
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        damagePerMin DOUBLE PATH '$.challenges.damagePerMinute'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_dpm = result["avg_dpm"] if result else 0
        logger.info(f"Player's average DPM: {avg_dpm}")
        return avg_dpm
    except:
        logger.exception(f"Failed to calculate player's dpm for puuid: {puuid}")

def player_damage_percentage(conn, cursor, puuid):
    """ Returns player's damage percentage on team
        Params: puuid: str
        Return: dmg_percent : float
    """
    try:    
        cursor.execute(
            """ SELECT AVG(p.dmg_percent) AS avg_dmg_percent
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        dmg_percent DOUBLE PATH '$.challenges.teamDamagePercentage'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_dmg = result["avg_dmg_percent"] if result else 0
        logger.info(f"Player's average DMG: {avg_dmg}")
        return avg_dmg
    except:
        logger.exception(f"Failed to calculate player's dmg % for puuid: {puuid}")

def player_kda(conn, cursor, puuid):
    """ Returns player's KDA
        Params: puuid: str
        Return: kda : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.kda) AS avg_kda
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        kda DOUBLE PATH '$.challenges.kda'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_kda = result["avg_kda"] if result else 0
        logger.info(f"Player's average KDA: {avg_kda}")
        return avg_kda
    except:
        logger.exception(f"Failed to calculate player's kda for puuid: {puuid}")

def player_solo_kills(conn, cursor, puuid):
    """ Returns player's solo kills
        Params: puuid: str
        Return: avg_solo_kills : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.soloKills) AS avg_solo_kills
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        soloKills DOUBLE PATH '$.challenges.soloKills'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_solo_kills = result["avg_solo_kills"] if result else 0
        return avg_solo_kills
        logger.info(f"Player's average solo kills: {avg_solo_kills}")
    except:
        logger.exception(f"Failed to calculate player's solo kills for puuid: {puuid}")

def player_kp(conn, cursor, puuid):
    """ Returns player's kill participation
        Params: puuid: str
        Return: avg_kp : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.kp) AS avg_kp
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        kp DOUBLE PATH '$.challenges.killParticipation'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_kp = result["avg_kp"] if result else 0
        logger.info(f"Player's average kill participation: {avg_kp}")
        return avg_kp
    except:
        logger.exception(f"Failed to calculate player's kill participation for puuid: {puuid}")

def calculate_player_aggression_stats(conn, cursor, puuid):
    """ Returns player's aggression stats
        Params: puuid: str
        Return: {"dmg_percent": 0.5, "dpm": 0.5, "kda": 0.5, "solo_kills": 0.5, "kp": 0.5}
    """
    try:
        dpm = player_damage_per_min(conn, cursor, puuid)
        dmg_percent = player_damage_percentage(conn, cursor, puuid)
        kda = player_kda(conn, cursor, puuid)
        solo_kills = player_solo_kills(conn, cursor, puuid)
        kp = player_kp(conn, cursor, puuid)

        res = {
            "dmg_percent": dmg_percent,
            "dpm": dpm,
            "kda": kda,
            "solo_kills": solo_kills,
            "kp": kp
        }
        logger.info(f"Player's aggression stats: {res}")
        return res
    except:
        logger.exception(f"Failed to calculate player's aggression stats for puuid: {puuid}")

def player_gold_per_min(conn, cursor, puuid):
    """ Returns player's gold/min
        Params: puuid: str
        Return: avg_gpm : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.gpm) AS avg_gpm
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        gpm DOUBLE PATH '$.challenges.goldPerMinute'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_gpm = result["avg_gpm"] if result else 0
        logger.info(f"Player's average gold per minute: {avg_gpm}")
        return avg_gpm
    except:
        logger.exception(f"Failed to calculate player's gold per min for puuid: {puuid}")

def player_gold_percentage(conn, cursor, puuid):
    """ Returns player's gold percentage on their team
        Params: puuid: str
        Return: gold_percent : float
    """
    try:
        cursor.execute(
            """
            SELECT AVG(player_gold / team_gold) AS avg_gold_percent
            FROM (
                SELECT 
                    m.matchId,
                    p.gold AS player_gold,
                    SUM(CASE WHEN p2.teamId = p.teamId THEN p2.gold ELSE 0 END) AS team_gold
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        gold DOUBLE PATH '$.goldEarned',
                        teamId INT PATH '$.teamId'
                    )
                ) AS p
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        gold DOUBLE PATH '$.goldEarned',
                        teamId INT PATH '$.teamId'
                    )
                ) AS p2 ON TRUE
                WHERE p.puuid = %s
                GROUP BY m.matchId, p.gold, p.teamId
            ) AS subquery
            """,
            (puuid,)
        )
        result = cursor.fetchone()
        avg_gold_percent = result["avg_gold_percent"] if result and result["avg_gold_percent"] is not None else 0
        logger.info(f"Player's average gold percentage on team: {avg_gold_percent}")
        return float(avg_gold_percent)
    except Exception:
        logger.exception(f"Failed to calculate player's gold percentage for puuid: {puuid}")
        return 0.0

def player_cs_per_min(conn, cursor, puuid):
    """ Returns player's average CS per minute including all minions
        Params: puuid: str
        Return: avg_cspm : float
    """
    try:
        cursor.execute(
            """
            SELECT AVG((p.total_cs + p.neutral_cs) / (j.gameDuration / 60)) AS avg_cspm
            FROM MatchData m
            JOIN JSON_TABLE(
                m.matchData,
                '$.info.participants[*]'
                COLUMNS (
                    puuid VARCHAR(100) PATH '$.puuid',
                    total_cs INTEGER PATH '$.totalMinionsKilled',
                    neutral_cs INTEGER PATH '$.neutralMinionsKilled'
                )
            ) AS p
            JOIN JSON_TABLE(
                m.matchData,
                '$.info'
                COLUMNS (
                    gameDuration DOUBLE PATH '$.gameDuration'
                )
            ) AS j
            WHERE p.puuid = %s
            """,
            (puuid,)
        )
        result = cursor.fetchone()
        avg_cspm = result["avg_cspm"] if result and result["avg_cspm"] is not None else 0
        logger.info(f"Player's average CS/min (including all jungle): {avg_cspm}")
        return float(avg_cspm)
    except Exception:
        logger.exception(f"Failed to calculate player's CS/min for puuid: {puuid}")
        return 0.0


def calculate_player_gold_income(conn, cursor, puuid):
    """ Returns player's gold income
        Params: puuid: str
        Return: {"gpm": 100, "gold_percentage": 20, "cspm": 8}
    """
    try:
        # Get player's gold per minute
        gpm = player_gold_per_min(conn, cursor, puuid)

        # Get player's gold percentage on their team
        gold_percentage = player_gold_percentage(conn, cursor, puuid)

        # Get player's CS/min
        cspm = player_cs_per_min(conn, cursor, puuid)

        res = {
            "gpm": gpm,
            "gold_percentage": gold_percentage,
            "cspm": cspm
        }
        return res
    except:
        logger.exception(f"Failed to calculate player's gold income stats for puuid: {puuid}")

def player_vision_per_min(conn, cursor, puuid):
    """ Returns player's vision per minute
        Params: puuid: str
        Return: avg_vpm : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.vpm) AS avg_vpm
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        vpm DOUBLE PATH '$.challenges.visionScorePerMinute'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_vpm = result["avg_vpm"] if result else 0
        logger.info(f"Player's average vision per minute: {avg_vpm}")
        return avg_vpm
    except:
        logger.exception(f"Failed to calculate player's vision per min for puuid: {puuid}")

def player_vision_score(conn, cursor, puuid):
    """ Returns player's vision score
        Params: puuid: str
        Return: avg_vision_score : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.visionScore) AS avg_vision_score
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        visionScore DOUBLE PATH '$.visionScore'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_vision_score = result["avg_vision_score"] if result else 0
        logger.info(f"Player's average vision score: {avg_vision_score}")
        return avg_vision_score
    except:
        logger.exception(f"Failed to calculate player's vision score for puuid: {puuid}")

def player_wards_cleared(conn, cursor, puuid):
    """ Returns player's wards cleared
        Params: puuid : str
        Return: avg_wards_cleared : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.wardsCleared) AS avg_wards_cleared
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        wardsCleared DOUBLE PATH '$.wardsKilled'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_wards_cleared = result["avg_wards_cleared"] if result else 0
        logger.info(f"Player's average wards cleared: {avg_wards_cleared}")
        return avg_wards_cleared
    except:
        logger.exception(f"Failed to calculate player's wards cleared for puuid: {puuid}")

def player_wards_placed(conn, cursor, puuid):
    """ Returns player's wards placed
        Params: puuid : str
        Return: avg_wards_placed : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.wardsPlaced) AS avg_wards_placed
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        wardsPlaced DOUBLE PATH '$.wardsPlaced'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_wards_placed = result["avg_wards_placed"] if result else 0
        logger.info(f"Player's average wards placed: {avg_wards_placed}")
        return avg_wards_placed
    except:
        logger.exception(f"Failed to calculate player's wards placed for puuid: {puuid}")

def calculate_player_vision_warding(conn, cursor, puuid):
    """ Returns player's vision/warding stats
        Params: puuid : str
        Return: {"avg_vpm": 0.5, "avg_vision_score": 0.5, "avg_wards_cleared": 2}
    """
    try:
        # Get player's vision per minute
        vpm = player_vision_per_min(conn, cursor, puuid)

        # Get player's average vision score
        avg_vision_score = player_vision_score(conn, cursor, puuid)

        # Get player's average wards cleared
        avg_wards_cleared = player_wards_cleared(conn, cursor, puuid)

        res = {
            "avg_vpm": vpm,
            "avg_vision_score": avg_vision_score,
            "avg_wards_cleared": avg_wards_cleared
        }
        return res
    except:
        logger.exception(f"Failed to calculate player's vision/wards stats for puuid: {puuid}")

def player_objective_damage(conn, cursor, puuid):
    """ Returns players damage dealt to objectives
        Params: puuid : str
        Return: avg_dmg_to_objectives : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.damageToObj) AS avg_dmg_to_objectives
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        damageToObj DOUBLE PATH '$.damageDealtToObjectives'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_dmg_to_objectives = result["avg_dmg_to_objectives"] if result else 0
        logger.info(f"Average damage dealt to objectives: {avg_dmg_to_objectives}")
        return avg_dmg_to_objectives
    except:
        logger.exception(f"Failed to calculate player's dmg to objectives for puuid: {puuid}")

def player_damage_to_turret(conn, cursor, puuid):
    """ Returns player's dmg dealt to turrets
        Params: puuid : str
        Return: avg_dmg_to_turrets : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.damageToTurret) AS avg_dmg_to_turrets
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        damageToTurret DOUBLE PATH '$.damageDealtToTurrets'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_dmg_to_turrets = result["avg_dmg_to_turrets"] if result else 0
        logger.info(f"Average damage dealt to turrets: {avg_dmg_to_turrets}")
        return avg_dmg_to_turrets
    except:
        logger.exception(f"Failed to calculate player's dmg to turrets for puuid: {puuid}")

def player_turret_takedowns(conn, cursor, puuid):
    """ Returns player's turret takedowns
        Params: puuid : str
        Return: avg_turret_takedowns : float
    """
    try:
        cursor.execute(
            """ SELECT AVG(p.turretTakedowns) AS avg_turret_takedowns
                FROM MatchData m
                JOIN JSON_TABLE(
                    m.matchData,
                    '$.info.participants[*]'
                    COLUMNS (
                        puuid VARCHAR(100) PATH '$.puuid',
                        turretTakedowns DOUBLE PATH '$.turretTakedowns'
                    )
                ) AS p
                WHERE p.puuid = %s
            """, (puuid,) )
        result = cursor.fetchone()
        avg_turret_takedowns = result["avg_turret_takedowns"] if result else 0
        logger.info(f"Player's average turret takedowns: {avg_turret_takedowns}")
        return avg_turret_takedowns
    except:
        logger.exception(f"Failed to calculate player's turret takedowns for puuid: {puuid}")

def calculate_player_objectives(conn, cursor, puuid):
    """ Returns player's objectives stats
        Params: puuid : str
        Return: {"avg_dmg_to_objectives": 0.5, "avg_dmg_to_turrets": 0.5, "avg_turret_takedowns": 2}
    """
    try:
        # Get player's dmg to objectives
        avg_dmg_to_objectives = player_objective_damage(conn, cursor, puuid)

        # Get player's dmg to turrets
        avg_dmg_to_turrets = player_damage_to_turret(conn, cursor, puuid)

        # Get player's turret takedowns
        avg_turret_takedowns = player_turret_takedowns(conn, cursor, puuid)

        res = {
            "avg_dmg_to_objectives": avg_dmg_to_objectives,
            "avg_dmg_to_turrets": avg_dmg_to_turrets,
            "avg_turret_takedowns": avg_turret_takedowns
        }
        return res
    except:
        logger.exception(f"Failed to calculate player's objectives stats for puuid: {puuid}")

def calculate_player_early_game(conn, cursor, puuid):
    pass

def calculate_player_stats(conn, cursor, puuid):
    """ Return player stats
        Params: puuid: str
        Return {"puuid": 'p5wz...askW4', "gameName": 'melon', "tagLine": '23333' , "role": [JUNGLE, BOTTOM]}
    """
    try:
        # Get player's primary/secondary role(s)
        main_roles = calculate_primary_role(conn, cursor, puuid)
        logger.info(f"Primary/secondary roles: {main_roles}")

        # Get player's top champions 
        top_champions = calculate_most_played_champions(conn, cursor, puuid, number_of_champions=6)
        logger.info(f"Top champions: {top_champions}")

        # Get player's winrate
        winrate = calculate_player_winrate(conn, cursor, puuid)
        logger.info(f"Winrate: {winrate}")

        # 1️⃣ Get player's aggression stats
        aggression_stats = calculate_player_aggression_stats(conn, cursor, puuid)

        # 2️⃣ Get player's gold/income stats
        income_stats = calculate_player_gold_income(conn, cursor, puuid)

        # 3️⃣ Get player's vision/warding stats
        vision_warding_stats = calculate_player_vision_warding(conn, cursor, puuid)

        # 4️⃣Get player's objectives stats
        objectives_stats = calculate_player_objectives(conn, cursor, puuid)

        # 5️⃣ Get player's early game stats
        early_game_stats = calculate_player_early_game(conn, cursor, puuid)

        res = {
            "puuid": puuid,
            "role": main_roles,
            "topChampions": top_champions,
            "winrate": winrate,
            "aggression": aggression_stats,
            "income": income_stats,
            "vision": vision_warding_stats,
            "objective": objectives_stats
        }
        return res
        
    except Exception as e:
        logger.exception(f"Failed to calculate player stats for puuid: {puuid}")

def upsert_player_stats(conn, cursor, puuid):
    data = calculate_player_stats(conn, cursor, puuid)
    try:
        cursor.execute(
            """ INSERT INTO PlayerStats (puuid, role, topChampions, winrate, aggression, income, vision, objective)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    role=VALUES(role),
                    topChampions=VALUES(topChampions),
                    winrate=VALUES(winrate),
                    aggression=VALUES(aggression),
                    income=VALUES(income),
                    vision=VALUES(vision),
                    objective=VALUES(objective)

            """,
            (puuid, json.dumps(data['role']), json.dumps(data['topChampions']), data['winrate'], json.dumps(data['aggression']), json.dumps(data['income']), json.dumps(data['vision']), json.dumps(data['objective']))
        )
        conn.commit()
        logger.info("Successfully inserted player into PlayerStats table!")
    except Exception as e:
        logger.exception("Failed to insert player stats")

# Two Step Query 
def calculate_role_stats2(conn, cursor, gameName, tagLine, puuid):
    """ Returns number of times role is played in descending order --- TWO STEP QUERY
        Params: gameName: str 
                tagLine: str
        Return: {BOTTOM: 27, TOP: 12, JUNGLE: 7, SUPPORT: 2, MIDDLE: 0} 
        SELECT JSON_UNQUOTE(
            JSON_EXTRACT(
                matchData,
                CONCAT(
                    '$.info.participants[',
                    REPLACE(REPLACE(
                        JSON_UNQUOTE(
                            JSON_SEARCH(
                                JSON_EXTRACT(matchData, '$.info.participants[*].puuid'),
                                'one',
                                '7xRZfjBRY8kSshE0pOG1_1ElDd7Xnr9iDddYKDKCdYpY6AK7l0MPcOKtWDGbGxG2uTO0FTJJ5E_acw'
                            )
                        ),
                        '$[', ''  -- remove $[
                    ), ']', ''),  -- remove trailing ]
                    '].lane'
                )
            )
        ) AS lane
        FROM MatchData
        WHERE matchId = 'NA1_5294635367';
    """
    # Query the role for every matchId
    match_ids = get_player_matchIds_by_puuid(conn, cursor, puuid)
    lanes = {
        'TOP': 0,
        'JUNGLE': 0,
        'MIDDLE': 0,
        'BOTTOM': 0,
        'SUPPORT': 0
    }
    try:
        total_start = time.time()           # Compare to One Step Query
        for match_id in match_ids:
            cursor.execute(
                """ SELECT JSON_UNQUOTE(
                    JSON_EXTRACT(
                        matchData,
                        CONCAT(
                            '$.info.participants[',
                            REPLACE(REPLACE(
                                JSON_UNQUOTE(
                                    JSON_SEARCH(
                                        JSON_EXTRACT(matchData, '$.info.participants[*].puuid'),
                                        'one',
                                        %s
                                    )
                                ),
                                '$[', ''  -- remove $[
                            ), ']', ''),  -- remove trailing ]
                            '].lane'
                        )
                    )
                ) AS lane
                FROM MatchData
                WHERE matchId = %s;
            """, ( puuid, match_id ) )
            role = cursor.fetchone()['lane']
            lanes[role] += 1
        logger.info(f"{gameName}#{tagLine}'s lane stats: {lanes}")
        total_end = time.time()
        logging.info(f"Total time for {len(match_ids)} queries: {total_end - total_start:.4f} seconds")
    except:
        logger.exception(f"Failed to calculate role stats for Player: {gameName}#{tagLine}")
        return {}

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
