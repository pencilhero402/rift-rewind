import os
import sqlite3
from flask import request, jsonify, Blueprint
from server.controllers.stats.endpoints.match import MatchController
from server.config.database import connect_to_database

from dotenv import load_dotenv
load_dotenv()

MATCH_PATH = os.getenv("MATCHES_DIR")
matches_bp = Blueprint("matches", __name__)

# Display all matches in Match Table
@matches_bp.route('/matches', methods=['GET'])
def getMatches():
    m = MatchController()
    matches = m.getMatches()
    return jsonify(matches)

# Add match to match Table
@matches_bp.route('/matches', methods=['POST'])
def createMatches():
    data = request.json
    if not data or "gameName" not in data or "tagLine" not in data:
        return jsonify({"success": False, "error": "Missing gameName or tagLine"}), 400
    m = MatchController(gameName=data["gameName"], tagLine=data["tagLine"])
    result = m.createMatches()
    return jsonify(result)
