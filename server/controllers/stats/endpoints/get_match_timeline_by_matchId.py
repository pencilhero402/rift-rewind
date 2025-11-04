from ._base import Endpoint
from server.controllers.stats.library._http import RiotStatsHTTP
from urllib.parse import quote

class MatchTimelineByMatchID(Endpoint):
    riot_http = RiotStatsHTTP()
    endpoint = "/lol/match/v5/matches/{matchId}/timeline"
    expected_data = {"matchId"}
    riot_response = None
    player_stats = None
    team_stats = None
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
        pass

""" ----- get_request ----- """
#a = MatchTimelineByMatchID(matchId="NA1_5395925069")
#print(a.get_request().get_dict())
        
            
