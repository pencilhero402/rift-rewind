import os
import sqlite3
from flask import request, jsonify, Blueprint
from server.controllers.stats.endpoints.player import PlayerController
from server.config.database import connect_to_database

from dotenv import load_dotenv
load_dotenv()

PLAYER_PATH = os.getenv("PLAYER_DIR")
players_bp = Blueprint("players", __name__)

# Display all players in Player Table
@players_bp.route('/players', methods=['GET'])
def getPlayers():
    p = PlayerController()
    players = p.getPlayers()
    return jsonify(players)

# Add player to Player Table
@players_bp.route('/players', methods=['POST'])
def createPlayer():
    data = request.json
    if not data or "gameName" not in data or "tagLine" not in data:
        return jsonify({"success": False, "error": "Missing gameName or tagLine"}), 400
    p = PlayerController(gameName=data["gameName"], tagLine=data["tagLine"])
    result = p.createPlayer()
    return jsonify(result)

# Get Player by gameName and tagLine
@players_bp.route('/players/<gameName>/<tagLine>', methods=['GET'])
def getPlayerByNameAndTag(gameName, tagLine):
    if not gameName or not tagLine:
        return jsonify({"success": False, "error": "Missing gameName or tagLine"}), 400
    conn, cursor = connect_to_database(PLAYER_PATH)
    if conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    player = None
    
    if conn and cursor:
        cursor.execute("SELECT * FROM Player WHERE gameName=? and tagLine=?", (gameName, tagLine))
        player = cursor.fetchone()
        conn.close()
    
    if player:
        return jsonify({"success": True, "player": dict(player)})
    else:
        return jsonify({"success": False, "error": "Player not found"}), 404
    
@players_bp.route('/players/<puuid>/', methods=['GET'])
def getPlayerByPUUID(puuid):
    if not puuid:
        return jsonify({"success": False, "error": "Missing puuid"}), 400
    conn, cursor = connect_to_database(PLAYER_PATH)
    if conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    player = None
    
    if conn and cursor:
        cursor.execute("SELECT * FROM Player WHERE puuid=?", (puuid,))
        player = cursor.fetchone()
        conn.close()
    
    if player:
        return jsonify({"success": True, "player": dict(player)})
    else:
        return jsonify({"sucess": False, "erorr": "Player not found"}), 404