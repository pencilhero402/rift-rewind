from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Initialize Flask
app = Flask(__name__)
PORT = int(os.getenv("PORT", 5001))

# Middleware
CORS(app)  # equivalent to express cors
app.config['JSON_SORT_KEYS'] = False  # optional: preserve JSON key order

# Import and register routes
from server.routes.players import players_bp
from server.routes.matches import matches_bp
from server.routes.matchesData import matchData_bp

app.register_blueprint(players_bp, url_prefix="/api")
app.register_blueprint(matches_bp, url_prefix="/api")
app.register_blueprint(matchData_bp, url_prefix="/api")

# Root route
@app.route("/")
def root():
    return '<h1 style="text-align: center; margin-top: 50px;">Rift Rewind</h1>', 200

# Start server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)