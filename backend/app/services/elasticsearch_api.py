import json
from pprint import pprint

from fastapi.encoders import jsonable_encoder
from app.core.config import vyper_config
from elasticsearch import Elasticsearch
from elasticsearch import AsyncElasticsearch



class Elasticsearch_API():
	# add error message for unauthorized user

	def __init__(self):
		self.cfg = vyper_config()
		self.url = self.cfg.get('elasticsearch.url')
		self.indice = self.cfg.get('elasticsearch.indice')

		if self.cfg.is_set('elasticsearch.username') and self.cfg.is_set('elasticsearch.password'):
			self.es = AsyncElasticsearch(
				self.url,
				http_auth=(self.cfg.get('elasticsearch.username'),
						self.cfg.get('elasticsearch.password'))
				)
		else:
			self.es = AsyncElasticsearch(self.url)


	async def post(self, query: dict):
		# json_query = json.dumps(jsonable_encoder(query))
		
		response = {}
		# try:
		response = await self.es.search(index=self.indice, 
			body=query,
			size=1000)
		# except:
			# print("Forward proxy had an error while forwarding")

		return response


	async def close(self):
		await self.es.close()



if __name__ == '__main__':
	es = Elasticsearch_API()