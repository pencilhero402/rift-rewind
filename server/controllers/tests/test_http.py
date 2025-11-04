import pytest
import requests
from ..riot_api._http import RiotHTTP, RiotResponse

#@pytest.fixture
def mock_session():
    session = RiotHTTP()    
    session2 = RiotHTTP()
    print(session.get_session())
    print(session2.get_session())
    
mock_session()