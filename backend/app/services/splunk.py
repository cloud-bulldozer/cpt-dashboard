import orjson
from app import config
from splunklib import client, results
import asyncio
from app.api.v1.commons.constants import SPLUNK_SEMAPHORE_COUNT

SEMAPHORE = asyncio.Semaphore(SPLUNK_SEMAPHORE_COUNT)


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

    def build_search_query(self, searchList=""):
        search_query = f"search index={self.indice} "

        if searchList:
            search_query += f"{searchList} "
        search_query += "| eventstats count AS total_records | fields total_records _raw host source sourcetype _bkt _serial _indextime"

        return search_query

    async def query(self, query, searchList="", size=100, offset=0, max_results=10000):
        """
        Query data from splunk server using splunk lib sdk

        Args:
            query (string): splunk query
            OPTIONAL: searchList (string): additional query parameters for index
        """
        query.update({"count": size, "offset": offset})
        search_query = self.build_search_query(searchList)

        try:

            async with SEMAPHORE:
                try:
                    oneshot_results = await asyncio.to_thread(
                        self.service.jobs.oneshot,
                        search_query,
                        **query,
                    )

                    if not oneshot_results:
                        return {"data": [], "total": 0}

                    # Process results using an async generator
                    res_array = []
                    total_records = 0
                    async for record in self._stream_results(oneshot_results):
                        try:
                            raw_data = record.get("_raw", "{}")
                            res_array.append(
                                {
                                    "data": orjson.loads(raw_data),
                                    "host": record.get("host", ""),
                                    "source": record.get("source", ""),
                                    "sourcetype": record.get("sourcetype", ""),
                                    "bucket": record.get("_bkt", ""),
                                    "serial": record.get("_serial", ""),
                                    "timestamp": record.get("_indextime", ""),
                                }
                            )
                        except Exception as e:
                            print(f"Error processing record: {e}")

                    return {
                        "data": res_array,
                        "total": int(record.get("total_records", 0)),
                    }

                except Exception as e:
                    print(f"Error querying Splunk: {e}")
                    return None

        except Exception as e:
            print("Error querying splunk: {}".format(e))
            return None

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

        async with SEMAPHORE:
            try:
                # If additional search parameters are provided, include those in searchindex
                search_query = f"search index={self.indice} "

                if searchList:
                    search_query += f"{searchList} "

                search_query += (
                    "| stats count AS total_records, "
                    "values(cpu) AS cpu, "
                    "values(node_name) AS nodeName, "
                    "values(test_type) AS benchmark, "
                    "values(ocp_version) AS ocpVersion, "
                    "values(ocp_build) AS releaseStream, "
                    "values(formal) AS isFormal, "
                    'count(eval(status="passed")) AS pass_count,'
                    'count(eval(like(status,"fail%"))) AS fail_count'
                    "| fields cpu, nodeName, benchmark, ocpVersion, releaseStream, isFormal, total_records, pass_count, fail_count, jobStatus"
                )

                # Run Splunk search asynchronously using `oneshot`
                results_reader = await asyncio.to_thread(
                    self.service.jobs.oneshot,
                    search_query,
                    earliest_time=query["earliest_time"],
                    latest_time=query["latest_time"],
                    output_mode="json",
                )

                # Parse the results
                decoded_data = orjson.loads(results_reader.read())
                value = decoded_data.get("results", [])
                total_records = int(value[0].get("total_records", 0)) if value else 0
                pass_count = int(value[0].get("pass_count", 0)) if value else 0
                fail_count = int(value[0].get("fail_count", 0)) if value else 0

                return {
                    "data": value,
                    "total": total_records,
                    "summary": {
                        "total": total_records,
                        "success": pass_count,
                        "failure": fail_count,
                    },
                }
            except Exception as e:
                print(f"Error on building data for filters: {e}")

    async def close(self):
        """Closes splunk client connections"""
        await self.service.logout()
