from decimal import Decimal
from datetime import datetime, date
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUMMONER_SPELLS = {
        1: "Cleanse",
        3: "Exhaust",
        4: "Flash",
        6: "Ghost",
        7: "Heal",
        11: "Smite",
        12: "Teleport",
        14: "Ignite",
        21: "Barrier",
}

RUNES = {
        # ------ Precision ------
        8000: "Precision",
        8005: "Press the Attack",
        8008: "Lethal Tempo",
        8010: "Conqueror",
        8021: "Fleet Footwork",
        # ----- Domination ------
        8100: "Domination",
        8112: "Electrocute",
        8124: "Predator",
        8128: "Dark Harvest",
        9923: "Hail of Blades",
        # ------ Sorcery  ------
        8200: "Sorcery",
        8214: "Summon Aery",
        8229: "Arcane Comet",
        8230: "Phase Rush",
        # ------ Inspiration ------
        8300: "Inspiration",
        8351: "Glacial Augment",
        8358: "Unsealed Spellbook",
        8360: "Prototype: Omnistone",
        8369: "First Strike",
        # ------ Resolve ------
        8400: "Resolve",
        8437: "Grasp of the Undying",
        8439: "Guardian",
        8465: "Aftershock",
}

ALL_COLUMNS = []

def format_match_data_by_player(rows, columns):
    """ Formats ALL rows in player's match history data
    """

    matches = {}
    for match in rows:
        match_data = {}

        player_list = match['summonerNames'].split(',')
        champion_list = match['championNames'].split(',')
        outcome_list = match['outcomes'].split(', ')[0].split(',')
        lane_list = match['lanes'].split(',')
        role_list = match['roles'].split(',')
        summonerSpell1_list = match['summonerSpells1'].split(',')
        summonerSpell2_list = match['summonerSpells2'].split(',')
        primaryRune_list = json.loads(match['primaryStyles'])
        secondaryRune_list = json.loads(match['secondaryStyles'])
        primaryKeystones_list = json.loads(match['primaryKeystones'])
        kills = match['kills'].split(',')
        deaths = match['deaths'].split(',')
        assists = match['assists'].split(',')
        kda_list = match['kda'].split(',')
        #kda_percentile = match['player_kda_percentile'] if match['player_kda_percentile'] is not None else None
        
        item0_list = match['item0'].split(',')
        item1_list = match['item1'].split(',')
        item2_list = match['item2'].split(',')
        item3_list = match['item3'].split(',')
        item4_list = match['item4'].split(',')
        item5_list = match['item5'].split(',')
        item6_list = match['item6'].split(',')

        teamId_list = match['teamIds'].split(',')

        participants = []       

        for idx, player in enumerate(player_list):
            summonerSpells = []
            summonerSpells.append({
                0 : SUMMONER_SPELLS[int(summonerSpell1_list[idx])],
                1 : SUMMONER_SPELLS[int(summonerSpell2_list[idx])]
            })

            if lane_list[idx] == 'BOTTOM':
                if role_list[idx] == 'CARRY':
                    lane_list[idx] = 'ADC'
                elif role_list[idx] == 'SUPPORT':
                    lane_list[idx] = 'SUPPORT'

            participants.append({
                'player': player,
                'champion': champion_list[idx],
                'outcome': int(outcome_list[idx]),
                'lane': lane_list[idx],
                'summonerSpells': summonerSpells,
                'runes': {
                    'primary': RUNES[primaryRune_list[idx]],
                    'keystone': RUNES[primaryKeystones_list[idx]],
                    'secondary': RUNES[secondaryRune_list[idx]]
                },
                'kda' : {
                    'kda': round(float(kda_list[idx]), 2),
                    #'kda_percentile': float(kda_percentile[idx]),
                    'kills': int(kills[idx]),
                    'deaths': int(deaths[idx]),
                    'assists': int(assists[idx])
                },
                'items': {
                    'item0': int(item0_list[idx]),
                    'item1': int(item1_list[idx]),
                    'item2': int(item2_list[idx]),
                    'item3': int(item3_list[idx]),
                    'item4': int(item4_list[idx]),
                    'item5': int(item5_list[idx]),
                    'item6': int(item6_list[idx])
                },
                'teamId': int(teamId_list[idx])
            })
        
        matchId = match['matchId']

        # Game Creation Format
        gameCreation = match['gameStartTimestamp']
        gameCreation_seconds = int(gameCreation) / 1000
        game_datetime = datetime.utcfromtimestamp(gameCreation_seconds)
        game_time_str = game_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Game Duration Format
        game_duration = match['gameDuration']
        minutes = game_duration // 60
        seconds = game_duration % 60
        formatted_game_duration = f"{minutes}:{seconds:02d}" 


        match_data['matchId'] = matchId
        match_data['gameCreation'] = game_time_str
        match_data['gameDuration'] = formatted_game_duration
        match_data['participants'] = participants

        matches[matchId] = (match_data)

    return matches

def format_aggregate_champion_stats(rows, columns=None):
    """ Formats ALL champion stats in AggregateChampionStats table
     champion_id | champion_name | kp       | dpm     | solo_kills | 
     dmg_percent | gpm     | cspm    | gold_percentage | avg_vpm  | avg_vision_score
      | avg_wards_cleared | avg_dmg_to_turrets | avg_turret_takedowns | games_played | last_updated
    """
    champions = {}
    for champion in rows:
        champion_id = champion['champion_id']
        champion_name = champion['champion_name']
        champion_kp = champion['kp']
        champion_dpm = champion['dpm']
        champion_solo_kills = champion['solo_kills']
        champion_dmg_percent = champion['dmg_percent']
        champion_gpm = champion['gpm']
        champion_cspm = champion['cspm']
        champion_gold_percentage = champion['gold_percentage']
        champion_avg_vpm = champion['avg_vpm']
        champion_avg_vision_score = champion['avg_vision_score']
        champion_avg_wards_cleared = champion['avg_wards_cleared']
        champion_avg_dmg_to_turrets = champion['avg_dmg_to_turrets']
        champion_avg_turret_takedowns = champion['avg_turret_takedowns']
        champion_games_played = champion['games_played']
        champion_last_updated = champion['last_updated']

         # Convert datetime to string if it is a datetime object
        if isinstance(champion_last_updated, (datetime, date)):
            champion_last_updated = champion_last_updated.strftime("%Y-%m-%d %H:%M:%S")

        champions[champion_id] = {
            'champion_id': champion_id,
            'champion_name': champion_name,
            'kp': champion_kp,
            'dpm': champion_dpm,
            'solo_kills': champion_solo_kills,
            'dmg_percent': champion_dmg_percent,
            'gpm': champion_gpm,
            'cspm': champion_cspm,
            'gold_percentage': champion_gold_percentage,
            'avg_vpm': champion_avg_vpm,
            'avg_vision_score': champion_avg_vision_score,
            'avg_wards_cleared': champion_avg_wards_cleared,
            'avg_dmg_to_turrets': champion_avg_dmg_to_turrets,
            'avg_turret_takedowns': champion_avg_turret_takedowns,
            'games_played': champion_games_played,
            'last_updated': champion_last_updated
        }
    return champions