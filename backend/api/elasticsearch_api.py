import json

from fastapi.encoders import jsonable_encoder
from config import get_server_config
from elasticsearch import Elasticsearch

class Elasticsearch_API():
	def __init__(self):
		try:
			self.config = get_server_config()
			self.url = self.config['elasticsearch']['url']
			self.indice = self.config['elasticsearch']['indice']
			self.user = self.config['elasticsearch']['username']
			self.password = self.config['elasticsearch']['password']

			self.es = Elasticsearch(self.url, http_auth=(self.user, self.password))
		except:
			print("Elasticsearch url undefined")

	def post(self, query):

		json_query = json.dumps(jsonable_encoder(query))
		response = {}

		try:
			response = self.es.search(index=self.indice, body=json_query)
		except:
			print("Forward proxy had an error while forwarding")

		return response