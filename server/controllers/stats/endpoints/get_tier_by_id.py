import logging
from ._base import Endpoint
from server.controllers.stats.library._http import RiotStatsHTTP
from urllib.parse import quote

class getTierById(Endpoint):
    riot_http = RiotStatsHTTP(base_url="https://na1.api.riotgames.com/{endpoint}")
    endpoint = "/lol/league/v4/entries/by-puuid/{encryptedPUUID}"
    expected_data = [{
        "leagueId": "c688999e-72b9-4160-98e2-6c5398af062d",
        "queueType": "RANKED_SOLO_5x5",
        "tier": "EMERALD",
        "rank": "II",
        "puuid": "WZSBB-fNv18VrM2z1d5mFxtpRm1J3gMftXGWqb657div_icbwx8ejNDs_psVvcq7KbpX-_abc4HAhQ",
        "leaguePoints": 25,
        "wins": 35,
        "losses": 32,
        "veteran": False,
        "inactive": False,
        "freshBlood": False,
        "hotStreak": False
    }]
    riot_response = None
    player_stats = None
    team_stats = None
    data_sets = None
    headers = None
    
    def __init__(self, encryptedPUUID=None, proxy=None, headers=None, timeout=30, get_request=True):
        self.encryptedPUUID = encryptedPUUID
        self.proxy = proxy
        
        if headers is not None:
            self.headers = headers
        self.timeout = timeout
        self.parameters = {}
        if get_request:
            self.get_request()
    
    def get_request(self):
        formatted_endpoint = self.endpoint.format(encryptedPUUID=self.encryptedPUUID)
        self.riot_response = self.riot_http.send_api_request(
            endpoint=formatted_endpoint,
            parameters=self.parameters,
            proxy=self.proxy,
            headers=self.headers,
            timeout=self.timeout,
        )
        return self.riot_response
        # self.load_response()
    
    # Parse response for certain columns
    def load_response(self):
        res = {}
        if self.riot_response is not None:
            riot_data = self.riot_response.get_dict()
            entry = riot_data[0]
            res["tier"] = entry.get("tier")
        else:
            logging.error("No response received.")
        return res

""" ----- get_request ----- """
#a = getTierById(puuid="")
#print(a.get_request().get_dict())
        
            
