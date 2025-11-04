from . import _http
import os

from dotenv import load_dotenv
load_dotenv()

STATS_HEADERS = {
    "X-Riot-Token": os.getenv("RIOT_API_KEY"),
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com"
}

class RiotStatsHTTP(_http.RiotHTTP):
    riot_response = _http.RiotHTTP
    headers = STATS_HEADERS
    
    def __init__(self, base_url="https://americas.api.riotgames.com/{endpoint}"):
        self.base_url = base_url

    def clean_contents(self, contents):
        if '{"Message":"An error has occurred."}' in contents:
            return "<Error><Message>An error has occurred.</Message></Error>"
        return contents
    
r = RiotStatsHTTP()
print(r.riot_response.parameters)