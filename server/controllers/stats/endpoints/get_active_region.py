import logging
from ._base import Endpoint
from server.controllers.stats.library._http import RiotStatsHTTP
from urllib.parse import quote


class ActiveRegion(Endpoint):
    riot_http = RiotStatsHTTP()
    endpoint = "/riot/account/v1/region/by-game/{game}/by-puuid/{puuid}"
    expected_data = {
        "puuid",
        "game",
        "region"
    }
    riot_response = None
    data_sets = None
    headers = None
    
    def __init__(self, game=None, puuid=None, proxy=None, headers=None, timeout=30, get_request=True):
        self.game = game
        self.puuid = puuid
        self.proxy = proxy
        
        if headers is not None:
            self.headers = headers
        self.timeout = timeout
        self.parameters = {}
        if get_request:
            self.get_request()
    
    def get_request(self):
        formatted_endpoint = self.endpoint.format(game=self.game, puuid=self.puuid)
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
            res["game"] = riot_dict["game"]
            res["region"] = riot_dict["region"]
        else:
            logging.error("No response received.")
        return res

""" ----- get_request ----- """
#a = ActiveRegion(game="lol", puuid="p5jMylPDjw3Q-rKszRu6Gm-c9qahO-CFp3g8hkgVvSh1uo7lzGTUo0fPjivcUXsHamM-m7amKZyKBw")
#print(a.get_request().get_dict())
        
            
