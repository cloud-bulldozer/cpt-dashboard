from app import config
import requests
from requests.auth import HTTPBasicAuth
import httpx


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

    async def async_get(self, path):
        async with httpx.AsyncClient(auth=(self.user, self.password)) as client:
            return await client.get(
              f'{self.base_url}/{path}'
            )

    def post(self, body, path):
        return requests.post(
          f"{self.base_url}/{path}", 
          data=body, 
          auth=HTTPBasicAuth(self.user, self.password)).json()

    def httpx_client(self):
        return httpx.AsyncClient(auth=(self.user, self.password))


