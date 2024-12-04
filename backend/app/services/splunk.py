import orjson
from app import config
from splunklib import client, results


class SplunkService:
    """
    Class to integrate splunk python client
    """

    def __init__(self, configpath="", index=""):
        """
        Initialize splunk client with provided config details

        Args:
            configpath (string): toml configuration path
            index (string): index name
        """
        try:
            cfg = config.get_config()
            if index == "":
                self.indice = cfg.get(configpath + ".indice")
            else:
                self.indice = index
            self.service = client.connect(
                host=cfg.get(configpath + ".host"),
                port=cfg.get(configpath + ".port"),
                username=cfg.get(configpath + ".username"),
                password=cfg.get(configpath + ".password"),
            )
        except Exception as e:
            print(f"Error connecting to splunk: {e}")
            return None

    async def query(self, query, searchList="", max_results=10000):
        """
        Query data from splunk server using splunk lib sdk

        Args:
            query (string): splunk query
            OPTIONAL: searchList (string): additional query parameters for index
        """
        query["count"] = max_results

        # If additional search parameters are provided, include those in searchindex
        searchindex = (
            "search index={} {}".format(self.indice, searchList)
            if searchList
            else "search index={}".format(self.indice)
        )
        try:
            oneshotsearch_results = self.service.jobs.oneshot(searchindex, **query)
        except Exception as e:
            print("Error querying splunk: {}".format(e))
            return None

        # Get the results and display them using the JSONResultsReader
        res_array = []
        async for record in self._stream_results(oneshotsearch_results):
            try:
                res_array.append(
                    {
                        "data": orjson.loads(record["_raw"]),
                        "host": record["host"],
                        "source": record["source"],
                        "sourcetype": record["sourcetype"],
                        "bucket": record["_bkt"],
                        "serial": record["_serial"],
                        "timestamp": record["_indextime"],
                    }
                )
            except Exception as e:
                print(f"Error on including Splunk record query in results array: {e}")

        return res_array

    async def _stream_results(self, oneshotsearch_results):
        for record in results.JSONResultsReader(oneshotsearch_results):
            yield record

    async def close(self):
        """Closes splunk client connections"""
        await self.service.logout()
