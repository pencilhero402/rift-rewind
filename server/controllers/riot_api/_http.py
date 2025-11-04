import os
import json
import random
import requests
import logging
from dotenv import load_dotenv

from urllib.parse import quote_plus

load_dotenv()

# Setup logging configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers= [
        logging.FileHandler("app.log"),  # Write logs to app.log
        logging.StreamHandler()  # Optionally also log to the console
    ]
)

STATS_HEADERS = {
    "X-Riot-Token": os.getenv("RIOT_API_KEY"),
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com"
}

class RiotResponse:
    def __init__(self, response, status_code, url):
        self._response = response
        self._status_code = status_code
        self._url = url

    def get_response(self):
        return self._response
    
    def get_dict(self):
        return json.loads(self._response)
    
    def get_json(self):
        return self.get_dict()
    
    def valid_json(self):
        try:
            self.get_dict()
        except ValueError:
            return False
        return True
    
    def get_url(self):
        return self._url

class RiotHTTP:
    riot_response = RiotResponse

    base_url = None
    
    parameters = None

    headers = None

    _session = None

    @classmethod
    def get_session(cls):
        session = cls._session
        if session is None:
            session = requests.Session()
            cls._session = session
        return session
    
    @classmethod
    def set_session(cls, session) -> None:
        cls._session = session

    def clean_contents(self, contents):
        return contents

    def send_api_request(self, endpoint, parameters, referer=None, proxy=None, headers=None, timeout=None, raise_exception_on_error=False):
        if not self.base_url:
            raise Exception("Cannot use send_api_request from _HTTP class")
        base_url = self.base_url.format(endpoint=endpoint)
        endpoint = endpoint.lower()
        self.parameters = parameters

        # Logging request details
        logging.info(f"Sending request to: {base_url}")
        logging.debug(f"Request parameters: {parameters}")
        logging.debug(f"Request headers: {headers}")

        parameters = sorted(parameters.items(), key=lambda kv: kv[0])

        request_headers = headers or self.headers or {}
        if referer:
            request_headers["Referer"] = referer
        
        proxies = None
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy
            }

        parameter_string = "&".join(
            "{}={}".format(key, "" if val is None else quote_plus(str(val)))
            for key, val in parameters
        )
        url = "{}?{}".format(base_url, parameter_string)

        logging.info(f"Full URL with parameters: {url}")  # Log the full URL
        print(url)

        try:
            # Send the request
            response = self.get_session().get(
                url=base_url,
                params=parameters,
                headers=request_headers,
                proxies=proxies,
                timeout=timeout
            )
            contents=response.text
            contents = self.clean_contents(contents)
            # Log the response status
            logging.info(f"Received response with status code: {response.status_code}")
            if response.status_code != 200:
                logging.error(f"Error response: {response.text}")

            # Log the response body content (be careful with sensitive data)
            logging.debug(f"Response content: {response.text}")

            # Create a RiotResponse object
            data = self.riot_response(response=contents, status_code=response.status_code, url=url)

            # Raise exception if needed
            if raise_exception_on_error and not data.valid_json():
                logging.error("Invalid response format")
                raise Exception("InvalidResponse: Response is not in a valid JSON format.")
            
            return data

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            raise