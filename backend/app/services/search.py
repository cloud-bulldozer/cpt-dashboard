from elasticsearch import AsyncElasticsearch
from fastapi.encoders import jsonable_encoder

from app import config


class ElasticService:
    # todo add bulkhead pattern
    # todo add error message for unauthorized user

    def __init__(self,airflow=False):
        self.cfg = config.get_config()
        if not airflow :
            self.url = self.cfg.get('elasticsearch.url')
            self.indice = self.cfg.get('elasticsearch.indice')
            if self.cfg.is_set('elasticsearch.username') and \
                    self.cfg.is_set('elasticsearch.password'):
                self.esUser = self.cfg.get('elasticsearch.username')
                self.esPass = self.cfg.get('elasticsearch.password')
        else :
            self.url = self.cfg.get('airflow_elasticsearch.url')
            self.indice = self.cfg.get('airflow_elasticsearch.indice')
            if self.cfg.is_set('airflow_elasticsearch.username') and \
                    self.cfg.is_set('airflow_elasticsearch.password'):
                self.esUser = self.cfg.get('airflow_elasticsearch.username')
                self.esPass = self.cfg.get('airflow_elasticsearch.password')

        if self.esUser :
            self.es = AsyncElasticsearch(
                    self.url,
                    use_ssl=False,
                    verify_certs=False,
                    http_auth=(self.esUser,self.esPass)
            )
        else:
            self.es = AsyncElasticsearch(self.url)

    async def post(self, query, indice=None):
        if indice is None:
            indice = self.indice
        return await self.es.search(
            index=indice,
            body=jsonable_encoder(query),
            size=1000)

    async def close(self):
        await self.es.close()
