from app import config
import requests
from requests.auth import HTTPBasicAuth
import httpx
import asks


class AirflowService:

    def __init__(self):
        self.cfg = config.get_config()
        self.base_url = self.cfg.get('airflow.url').rstrip("/")
        self.user = self.cfg.get('airflow.username')
        self.password = self.cfg.get('airflow.password')

    def get(self, path):
        return requests.get(
          f"{self.base_url}/{path}", 
          auth=HTTPBasicAuth(self.user, self.password)).json()

    def post(self, body, path):
        return requests.post(
          f"{self.base_url}/{path}", 
          data=body, 
          auth=HTTPBasicAuth(self.user, self.password)).json()

    def httpx_client(self):
        return httpx.AsyncClient(auth=(self.user, self.password))

    def asks_client(self):
        return asks.Session(
            connections=10
        )
