import json
import numpy as np
try:
    from pandas import DataFrame, MultiIndex

    PANDAS = True
except ImportError:
    PANDAS = False
    
from server.controllers.stats.library import _http

class Endpoint:
    def __init__(self, riot_response: _http.RiotStatsResponse):
        self.riot_response = riot_response
    class DataSet:
        key = None
        data = {}
        def __init__(self, data={}):
            self.data = data

        def get_json(self):
            return json.dumps(self.data)
        
        def get_dict(self):
            return self.data

    def get_request_url(self):
        """ Return URL with or without specific endpoints or query parameters """
        return self.riot_response.get_url()

    def get_response(self):
        """ Return response for requested URL """
        return self.riot_response.get_response()

    def get_dict(self):
        """ Convert response to dictionary """
        return self.riot_response.get_dict()

    def get_json(self):
        """ Return response as JSON string """
        return self.riot_response.get_json()
    