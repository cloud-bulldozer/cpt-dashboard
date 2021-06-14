import httpx

from app import config


class AirflowService:

    def __init__(self):
        self.cfg = config.get_config()
        self.base_url = self.cfg.get('airflow.url').rstrip("/")
        self.user = self.cfg.get('airflow.username')
        self.password = self.cfg.get('airflow.password')

    async def async_get(self, path):
        async with httpx.AsyncClient(auth=(self.user, self.password)) as client:
            return await client.get(
              f'{self.base_url}/{path}'
            )

    def post(self, body, path):
        return httpx.post(
          f"{self.base_url}/{path}", 
          data=body, 
          auth=(self.user, self.password)).json()

    def httpx_client(self):
        return httpx.AsyncClient(auth=(self.user, self.password))
