from fastapi.encoders import jsonable_encoder
from app import config

from elasticsearch import AsyncElasticsearch
import elasticsearch as es

class ElasticService:
	# add error message for unauthorized user

	def __init__(self):
		self.cfg = config.get_config()
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

	async def post(self, query, indice=None):
		response = {}
		if indice is None:
			indice = self.indice
		# try:
		response = await self.es.search(index=indice, 
			body=jsonable_encoder(query),
			size=1000)
		# except:
			# print("Forward proxy had an error while forwarding")
		return response

	async def close(self):
		await self.es.close()



if __name__ == '__main__':
	es = ElasticService()