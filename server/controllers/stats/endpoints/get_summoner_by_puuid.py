import logging
from ._base import Endpoint
from server.controllers.stats.library._http import RiotStatsHTTP
from urllib.parse import quote

class Summoner(Endpoint):
    riot_http = RiotStatsHTTP(base_url="https://na1.api.riotgames.com/{endpoint}")
    endpoint = "/lol/summoner/v4/summoners/by-puuid/{encryptedPUUID}"
    expected_data = {
        "puuid": "p5jMylPDjw3Q-rKszRu6Gm-c9qahO-CFp3g8hkgVvSh1uo7lzGTUo0fPjivcUXsHamM-m7amKZyKBw",
        "profileIconId": 3587,
        "revisionDate": 1761365141000,
        "summonerLevel": 503
    }
    riot_response = None
    data_sets = None
    headers = None
    
    def __init__(self, puuid=None, proxy=None, headers=None, timeout=30, get_request=True):
        self.puuid = puuid
        self.proxy = proxy
        
        if headers is not None:
            self.headers = headers
        self.timeout = timeout
        self.parameters = {}
        if get_request:
            self.get_request()
    
    def get_request(self):
        formatted_endpoint = self.endpoint.format(encryptedPUUID=self.puuid)
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
            res["profileIconId"] = riot_dict["profileIconId"]
            res["summonerLevel"] = riot_dict["summonerLevel"]
        else:
            logging.error("No response received.")
        return res

""" ----- get_request ----- """
#a = Summoner(puuid="p5jMylPDjw3Q-rKszRu6Gm-c9qahO-CFp3g8hkgVvSh1uo7lzGTUo0fPjivcUXsHamM-m7amKZyKBw")
#print(a.get_request().get_dict())
        
            
