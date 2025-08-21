import requests
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_BASE_URL, REQUEST_TIMEOUT


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL, timeout: int = REQUEST_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def get(self, path: str, token: str = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        resp = self.session.get(
            f"{self.base_url}{path}", 
            headers=headers, 
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
    
    def post(self, path: str, json: dict = None, token: str = None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        resp = self.session.post(
            f"{self.base_url}{path}", 
            headers=headers, 
            json=json or {},
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
    
    def put(self, path: str, json: dict = None, token: str = None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        resp = self.session.put(
            f"{self.base_url}{path}", 
            headers=headers, 
            json=json or {},
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
    
    def delete(self, path: str, token: str = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        resp = self.session.delete(
            f"{self.base_url}{path}", 
            headers=headers, 
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()


# Global API client instance
api_client = APIClient()
