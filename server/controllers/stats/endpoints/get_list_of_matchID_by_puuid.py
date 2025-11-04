import logging
from ._base import Endpoint
from server.controllers.stats.library._http import RiotStatsHTTP


class MatchIDsByPUUID(Endpoint):
    riot_http = RiotStatsHTTP()
    endpoint = "/lol/match/v5/matches/by-puuid/{puuid}/ids"
    expected_data = {"matchID"}
    riot_response = None
    data_sets = None
    headers = None
    
    def __init__(self, puuid=None, startTime=None, endTime=None, queue=None, type=None, start=0, count=20, proxy=None, headers=None, timeout=30, get_request=True):
        self.puuid = puuid
        self.proxy = proxy
        
        if headers is not None:
            self.headers = headers
        self.timeout = timeout
        self.parameters = {
            "startTime" : startTime,
            "endTime": endTime,
            "queue": queue,
            "type": type,
            "start": start,
            "count": count 
        }
        if get_request:
            self.get_request()
    
    def get_request(self):
        formatted_endpoint = self.endpoint.format(puuid=self.puuid)
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
        if self.riot_response is not None:
            riot_dict = self.riot_response.get_dict()
        else:
            logging.error("No response received.")
        return riot_dict

""" ----- get_request ----- """
#a = MatchIDsByPUUID("p5jMylPDjw3Q-rKszRu6Gm-c9qahO-CFp3g8hkgVvSh1uo7lzGTUo0fPjivcUXsHamM-m7amKZyKBw")
#print(a.load_response())
#print(type(a.load_response()))
        
            
