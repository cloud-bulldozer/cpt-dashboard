from elasticsearch import AsyncElasticsearch
from fastapi.encoders import jsonable_encoder

from app import config

import urllib3
urllib3.disable_warnings()

class ElasticService:
    # todo add bulkhead pattern
    # todo add error message for unauthorized user

    def __init__(self,configpath="",index=""):
        self.cfg = config.get_config()
        self.url = self.cfg.get(configpath+'.url')
        self.esUser = None
        if index == "":
            self.indice = self.cfg.get(configpath+'.indice')
        else:
            self.indice = index
        if self.cfg.is_set(configpath+'.username') and \
                self.cfg.is_set(configpath+'.password'):
            self.esUser = self.cfg.get(configpath+'.username')
            self.esPass = self.cfg.get(configpath+'.password')
        if self.esUser :
            self.es = AsyncElasticsearch(
                    self.url,
                    use_ssl=False,
                    verify_certs=False,
                    http_auth=(self.esUser,self.esPass)
            )
        else:
            self.es = AsyncElasticsearch(self.url, verify_certs=False)

    async def post(self, query, indice=None,size=10000):
        if indice is None:
            indice = self.indice
        return await self.es.search(
            index=indice,
            body=jsonable_encoder(query),
            size=size)

    async def close(self):
        await self.es.close()
