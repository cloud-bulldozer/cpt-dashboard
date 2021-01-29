import json

from fastapi.encoders import jsonable_encoder
from app.core.config import vyper_config
from elasticsearch import Elasticsearch


class Elasticsearch_API():
	# add error message for unauthorized user

	def __init__(self):
		self.cfg = vyper_config()
		self.url = self.cfg.get('elasticsearch.url')
		self.indice = self.cfg.get('elasticsearch.indice')
		self.es = Elasticsearch(
			self.url,
			http_auth=(self.cfg.get('elasticsearch.username'),
					   self.cfg.get('elasticsearch.password'))

		)

	def post(self, query):
		json_query = json.dumps(jsonable_encoder(query))
		response = {}

		# try:
		response = self.es.search(index=self.indice, body=json_query)
		# except:
			# print("Forward proxy had an error while forwarding")

		return response


if __name__ == '__main__':
	es = Elasticsearch_API()