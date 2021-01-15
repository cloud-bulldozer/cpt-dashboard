import requests
import json

from fastapi.encoders import jsonable_encoder

class Elasticsearch():
	def __init__(self):
		self.url = "https://search-perfscale-dev-chmf5l4sh66lvxbnadi4bznl3a.us-west-2.es.amazonaws.com/perf*/_search"
		self.headers = {'Content-Type': 'application/json'}

	def post(self, query):
		json_query = json.dumps(jsonable_encoder(query))
		try:
			response = requests.post(self.url, data=json_query, headers=self.headers)

		except:
			print("An exception occurred")
			response = {'Error': 'Forward proxy failed'}

		return response.json()