import orjson
from app import config
from splunklib import client, results
import json


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

    async def query(
        self, query, searchList="", size=None, offset=None, max_results=10000
    ):
        """
        Query data from splunk server using splunk lib sdk

        Args:
            query (string): splunk query
            OPTIONAL: searchList (string): additional query parameters for index
        """
        query["count"] = size
        query["offset"] = offset

        # If additional search parameters are provided, include those in searchindex
        searchindex = (
            "search index={} {}".format(self.indice, searchList)
            if searchList
            else "search index={}".format(self.indice)
        )

        search_query = (
            "search index={} {} | stats count AS total_records".format(
                self.indice, searchList
            )
            if searchList
            else "search index={} | stats count AS total_records".format(self.indice)
        )

        try:
            # Run the job and retrieve results
            job = await self.service.jobs.create(
                search_query,
                exec_mode="normal",
                earliest_time=query["earliest_time"],
                latest_time=query["latest_time"],
            )
            oneshotsearch_results = self.service.jobs.oneshot(searchindex, **query)
        except Exception as e:
            print("Error querying splunk: {}".format(e))
            return None

        # Fetch the results
        total_records = 0
        for result in job.results(output_mode="json"):
            decoded_data = json.loads(result.decode("utf-8"))
            value = decoded_data.get("results")
            total_records = value[0]["total_records"]

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

        return {"data": res_array, "total": total_records}

    async def _stream_results(self, oneshotsearch_results):
        for record in results.JSONResultsReader(oneshotsearch_results):
            yield record

    async def filterPost(self, query, searchList=""):
        """
        Query data to construct filter from splunk server using splunk lib sdk

        Args:
            query (string): splunk query
            OPTIONAL: searchList (string): additional query parameters for index
        """

        try:
            # If additional search parameters are provided, include those in searchindex
            searchindex = (
                f"search index={self.indice} {searchList}"
                if searchList
                else f"search index={self.indice}"
            )
            search_query = ""
            if searchList:
                search_query = "search index={} {} | stats count AS total_records, values(cpu) AS cpu, values(node_name) AS nodeName, values(test_type) AS benchmark, values(ocp_version) AS ocpVersion, values(ocp_build) AS releaseStream".format(
                    self.indice, searchList
                )
            else:
                search_query = "search index={} | stats count AS total_records, values(cpu) AS cpu, values(node_name) AS nodeName, values(test_type) AS benchmark, values(ocp_version) AS ocpVersion, values(ocp_build) AS releaseStream".format(
                    self.indice
                )

            try:
                # Run the job and retrieve results
                job = await self.service.jobs.create(
                    search_query,
                    exec_mode="blocking",
                    earliest_time=query["earliest_time"],
                    latest_time=query["latest_time"],
                )
            except Exception as e:
                print("Error querying in filters splunk: {}".format(e))
                return None

            value = []
            total_records = 0
            for result in job.results(output_mode="json"):
                decoded_data = json.loads(result.decode("utf-8"))
                value = decoded_data.get("results")
                total_records = value[0]["total_records"]

            return {"data": value, "total": total_records}
        except Exception as e:
            print(f"Error on building data for filters: {e}")

    async def close(self):
        """Closes splunk client connections"""
        await self.service.logout()
