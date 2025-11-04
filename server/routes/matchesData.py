import os
import sqlite3
from flask import request, jsonify, Blueprint
from server.controllers.stats.endpoints.matchData import MatchDataController
from server.config.database import connect_to_database

from dotenv import load_dotenv
load_dotenv()

MATCH_DATA_PATH = os.getenv("MATCH_DATA_DIR")
matchData_bp = Blueprint("match_data", __name__)

# Display all matches in Match Table
@matchData_bp.route('/match_data', methods=['GET'])
def getMatches():
    m = MatchDataController()
    matches = m.getAllMatchData()
    return jsonify(matches)

# Add match to match Table
