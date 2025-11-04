from server.controllers.riot_api import _http
from server.controllers.riot_api._http import STATS_HEADERS
import json

class RiotStatsResponse(_http.RiotResponse):
    def get_normalized_dict(self):
        pass

class RiotStatsHTTP(_http.RiotHTTP):
    riot_response = RiotStatsResponse
    
    headers = STATS_HEADERS
    
    def __init__(self, base_url="https://americas.api.riotgames.com/{endpoint}"):
        self.base_url = base_url

    def clean_contents(self, contents):
        if '{"Message":"An error has occurred."}' in contents:
            return "<Error><Message>An error has occurred.</Message></Error>"
        return contents