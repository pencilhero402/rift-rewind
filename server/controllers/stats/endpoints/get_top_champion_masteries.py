import logging
from ._base import Endpoint
from server.controllers.stats.library._http import RiotStatsHTTP
from urllib.parse import quote


class TopChampionMasteries(Endpoint):
    riot_http = RiotStatsHTTP(base_url="https://na1.api.riotgames.com/{endpoint}")
    endpoint = "lol/champion-mastery/v4/champion-masteries/by-puuid/{encryptedPUUID}/top"
    expected_data = {
        "puuid": "p5jMylPDjw3Q-rKszRu6Gm-c9qahO-CFp3g8hkgVvSh1uo7lzGTUo0fPjivcUXsHamM-m7amKZyKBw",
        "championId": 64,
        "championLevel": 15,
        "championPoints": 152061,
        "lastPlayTime": 1749096450000,
        "championPointsSinceLastLevel": 21461,
        "championPointsUntilNextLevel": -10461,
        "markRequiredForNextLevel": 2,
        "tokensEarned": 1,
        "championSeasonMilestone": 0,
        "nextSeasonMilestone": {
            "requireGradeCounts": {
                "A-": 1
            },
            "rewardMarks": 1,
            "bonus": False,
            "totalGamesRequires": 1
        }
    }
    riot_response = None
    data_sets = None
    headers = None
    
    def __init__(self, encryptedPUUID=None, count=3, proxy=None, headers=None, timeout=30, get_request=True):
        self.encryptedPUUID = encryptedPUUID
        self.count = count
        self.proxy = proxy
        
        if headers is not None:
            self.headers = headers
        self.timeout = timeout
        self.parameters = {
            "count" : count
        }
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
            riot_dict = self.riot_response.get_dict()
            res["puuid"] = riot_dict["puuid"]
            res["championId"] = riot_dict["championId"]
            res["championLevel"] = riot_dict["championLevel"]
        else:
            logging.error("No response received.")
        return res

""" ----- get_request ----- """
#a = TopChampionMasteries(encryptedPUUID="p5jMylPDjw3Q-rKszRu6Gm-c9qahO-CFp3g8hkgVvSh1uo7lzGTUo0fPjivcUXsHamM-m7amKZyKBw")
#print(a.get_request().get_json())
        
            
