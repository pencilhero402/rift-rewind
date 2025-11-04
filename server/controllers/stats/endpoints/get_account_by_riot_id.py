from ._base import Endpoint
import logging
from server.controllers.stats.library._http import RiotStatsHTTP
from urllib.parse import quote

class AccountByRiotID(Endpoint):
    riot_http = RiotStatsHTTP()
    endpoint = "/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    expected_data = {
        "puuid",
        "gameName",
        "tagLine"
    }
    riot_response = None
    data_sets = None
    headers = None
    
    def __init__(self, gameName=None, tagLine=None, proxy=None, headers=None, timeout=30, get_request=True):
        self.gameName = gameName
        self.tagLine = tagLine
        self.proxy = proxy
        
        if headers is not None:
            self.headers = headers
        self.timeout = timeout
        self.parameters = {}
        if get_request:
            self.get_request()
    
    def get_request(self):
        formatted_endpoint = self.endpoint.format(gameName=self.gameName, tagLine=self.tagLine)
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
            res["gameName"] = riot_dict["gameName"]
            res["tagLine"] = riot_dict["tagLine"]
        else:
            logging.error("No response received.")
        return res