import logging
import json
from ._base import Endpoint
from server.controllers.stats.library._http import RiotStatsHTTP
from urllib.parse import quote


class MatchByMatchID(Endpoint):
    riot_http = RiotStatsHTTP()
    endpoint = "/lol/match/v5/matches/{matchId}"
    expected_data = {"matchID"}
    riot_response = None
    data_sets = None
    headers = None
    
    def __init__(self, matchId=None, proxy=None, headers=None, timeout=30, get_request=True):
        self.matchId = matchId
        self.proxy = proxy
        
        if headers is not None:
            self.headers = headers
        self.timeout = timeout
        self.parameters = {}
        if get_request:
            self.get_request()
    
    def get_request(self):
        formatted_endpoint = self.endpoint.format(matchId=self.matchId)
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
        if self.riot_response:
            return self.riot_response.get_json()
        return None

""" ----- get_request ----- """
"""a = MatchByMatchID(matchId="NA1_5395925069").get_json()
with open("match.json", 'w') as file:
    json.dump(a, file, indent=4)"""
        
            
