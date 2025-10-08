from collections import defaultdict
from dataclasses import dataclass, field
import platform
import time
from typing import Annotated, Any, Optional

from app.api.v1.commons.constants import AGG_BUCKET_SIZE, MAX_PAGE
from fastapi import APIRouter, Depends
from app.services.search import ElasticService


router = APIRouter()

"""Information about OCP release KPIs.

Each product version has a set of benchmarks that have been run for various
system configurations. This data is recovered from the job index and used to
access average and historical data for a product version to help assess
product release readiness.

NOTE: Other factors directly affecting release health include the health of the
CI system, and any open Jira stories or bugs. Those factors aren't handled by
this code.

AI assistance: Cursor is extremely helpful in generating suggesting code
snippets along the way. While most of this code is hand generated as the
relationships are tricky and difficult to describe to the AI, it's been
extremely helpful as an "over the shoulder assistant" to simplify routine
coding tasks.

Assisted-by: Cursor + claude-4-sonnet
"""


# This is a mapping of benchmark names to the index they're stored in.
# This was generated from an exhaustive query for all benchmrk names.
# I additionally attempted to identify which indices were associated with
# each benchmark by searching for matching UUID values. I was unable to
# find matches for most benchmarks in any of the "ospst-" indices, which
# is why they're mapped to empty strings. It's possible that these
# benchmarks are obsolete, or their OpenSearch job documents are broken,
# or their indices don't appear in the INTLAB OpenSearch instance.
@dataclass
class Benchmark:
    index: str
    filter: dict[str, str] | None = None


BENCHMARK_INDEX: dict[str, Benchmark | None] = {
    "amadeus-mgob-usecase": None,
    "amadeus-usecase": None,
    "cluster-density": Benchmark(
        index="ripsaw-kube-burner",
        filter={
            "metricName.keyword": "podLatencyQuantilesMeasurement",
            "quantileName.keyword": "Ready",
        },
    ),
    "cluster-density-v2": Benchmark(
        index="ripsaw-kube-burner",
        filter={
            "metricName.keyword": "podLatencyQuantilesMeasurement",
            "quantileName.keyword": "Ready",
        },
    ),
    "concurrent-builds": None,
    "crd-scale": None,
    "custom": None,
    "index": None,
    "ingress-perf": Benchmark("ingress-performance"),
    "k8s-netperf": Benchmark("k8s-netperf"),
    "kueue-operator-jobs": None,
    "kueue-operator-jobs-shared": None,
    "kueue-operator-pods": Benchmark(
        index="ripsaw-kube-burner",
        filter={
            "metricName.keyword": "podLatencyQuantilesMeasurement",
            "quantileName.keyword": "Ready",
        },
    ),
    "large-networkpolicy-egress": None,
    "network-policy": None,
    "networkpolicy-case1": None,
    "networkpolicy-case2": None,
    "networkpolicy-case-amadeus-mgob": None,
    "node-density": None,
    "node-density-cni": None,
    "node-density-cni-networkpolicy": None,
    "node-density-heavy": None,
    "olm": Benchmark(
        index="ripsaw-kube-burner",
        filter={
            "metricName.keyword": "podLatencyQuantilesMeasurement",
            "quantileName.keyword": "Ready",
        },
    ),
    "ols-load-generator": None,
    "ovn-live-migration": None,
    "rds-core": None,
    "router-perf": None,
    "udn-density-l3-pods": None,
    "udn-density-pods": None,
    "virt-density": Benchmark(
        index="ripsaw-kube-burner",
        filter={
            "metricName.keyword": "vmiLatencyQuantilesMeasurement",
            "quantileName.keyword": "VMReady",
        },
    ),
    "virt-udn-density": None,
    "web-burner-cluster-density": None,
    "web-burner-init": None,
    "web-burner-node-density": None,
    "workers-scale": None,
}


@dataclass
class Fingerprint:
    masterNodesType: str
    masterNodesCount: int
    workerNodesType: str
    workerNodesCount: int
    platform: str

    @classmethod
    def parse(cls, node: dict[str, str]):
        return cls(
            node["masterNodesType"],
            int(node["masterNodesCount"]),
            node["workerNodesType"],
            int(node["workerNodesCount"]),
            node["platform"],
        )

    def __str__(self):
        return (
            f"mnt={self.masterNodesType}:mnc={self.masterNodesCount}"
            + f":wnt={self.workerNodesType}:wnc={self.masterNodesCount}"
            + f":p={self.platform}"
        )

    def json(self) -> dict[str, str | int]:
        return {
            "masterNodesType": self.masterNodesType,
            "masterNodesCount": self.masterNodesCount,
            "workerNodesType": self.workerNodesType,
            "workerNodesCount": self.workerNodesCount,
            "platform": self.platform,
        }


@dataclass
class Cache:
    """short_version: list[long_version]"""

    version_map: dict[str, list[str]] = field(default_factory=dict)

    """ version: {benchmark: {configuration: list[tuple], uuids: list[uuid]}} """
    benchmark_map: dict[str, dict[str, Any]] = field(default_factory=dict)


class KPI:
    product: str
    version: list[str]
    benchmarks: list[str]
    service: ElasticService
    cache: Cache

    @staticmethod
    def break_list(value: str | list[str] | None) -> list[str]:
        all = []
        if isinstance(value, str):
            all.extend(value.split(","))
        elif isinstance(value, list):
            for v in value:
                all.extend(v.split(","))
        return all

    def __init__(
        self,
        product: str,
        configpath: str = "ocp.elasticsearch",
        version: str | list[str] | None = None,
        benchmarks: list[str] | None = None,
    ):
        self.product = product
        self.version = self.break_list(version)
        self.benchmarks = self.break_list(benchmarks)
        self.service = ElasticService(configpath)
        print(f"opening service on {configpath}")
        self.cache = Cache()

    async def close(self):
        print("closing")
        await self.service.close()

    def get_index(self, benchmark: str) -> str | None:
        b = BENCHMARK_INDEX.get(benchmark)
        return b.index if b else None

    def get_filter(self, benchmark: str) -> dict[str, str] | None:
        b = BENCHMARK_INDEX.get(benchmark)
        return b.filter if b else None

    async def get_versions(self) -> dict[str, list[str]]:
        """Return a list of versions.

        Returns:
            The full version strings for each "short version" (e.g. "4.19").
        """
        if self.cache.version_map:
            return self.cache.version_map

        start = time.time()

        query = {
            "size": 0,
            "query": {"query_string": {"query": ('jobStatus: "success"')}},
            "aggs": {
                "versions": {
                    "terms": {
                        "field": "ocpVersion.keyword",
                        "size": AGG_BUCKET_SIZE,
                    },
                }
            },
        }
        response = await self.service.post(query=query, size=0)
        versions = defaultdict(set)
        for version in response["aggregations"]["versions"]["buckets"]:
            v = version["key"]
            versions[v[:4]].add(v)

        print(f"discovered versions: {time.time()-start:3f} seconds")
        self.cache.version_map = {k: sorted(v) for k, v in versions.items()}
        return self.cache.version_map

    async def get_benchmarks(self, version: str) -> dict[str, Any]:
        """Return a list of benchmarks run for a given OCP version.

        Args:
            version: The OCP version to get benchmarks for.

        Returns:
            A list of benchmarks and the configurations for which they were run.
        """

        query = {
            "size": 0,
            "query": {
                "query_string": {
                    "query": (f'jobStatus: "success" AND ocpVersion: {version}*')
                }
            },
            "aggs": {
                "configurations": {
                    "composite": {
                        "sources": [
                            {
                                "workerNodesType": {
                                    "terms": {"field": "workerNodesType.keyword"}
                                }
                            },
                            {
                                "masterNodesType": {
                                    "terms": {"field": "masterNodesType.keyword"}
                                }
                            },
                            {
                                "workerNodesCount": {
                                    "terms": {"field": "workerNodesCount"}
                                }
                            },
                            {
                                "masterNodesCount": {
                                    "terms": {"field": "masterNodesCount"}
                                }
                            },
                            {"platform": {"terms": {"field": "platform.keyword"}}},
                        ],
                        "size": 10000,
                    },
                    "aggs": {
                        "benchmarks": {
                            "terms": {
                                "field": "benchmark.keyword",
                                "size": AGG_BUCKET_SIZE,
                            },
                            "aggs": {
                                "uuids": {
                                    "terms": {
                                        "field": "uuid.keyword",
                                        "size": AGG_BUCKET_SIZE,
                                    }
                                },
                            },
                        }
                    },
                },
            },
        }
        start = time.time()
        if self.cache.benchmark_map and version in self.cache.benchmark_map:
            return self.cache.benchmark_map[version]
        response = await self.service.post(query=query, size=0)
        benchmarks = set()
        by_benchmark = defaultdict(list)
        for config in response["aggregations"]["configurations"]["buckets"]:
            bees = defaultdict(set)
            for benchmark in config["benchmarks"]["buckets"]:
                benchmarks.add(benchmark["key"])
                for uuid in benchmark["uuids"]["buckets"]:
                    bees[benchmark["key"]].add(uuid["key"])
            for b, u in bees.items():
                by_benchmark[b].append(
                    {
                        "configuration": Fingerprint.parse(config["key"]),
                        "uuids": list(u),
                    }
                )
                benchmarks.add(b)
        self.cache.benchmark_map[version] = dict(by_benchmark)
        print(
            f"discovered {version} benchmark hierarchy: {time.time()-start:3f} seconds"
        )
        return self.cache.benchmark_map[version]

    async def get_iterations(
        self,
    ) -> dict[str, Any]:
        """Break down our benchmark configuration data by job iterations.

        We can only compare benchmark metrics across the same configuration and job
        iteration count. While the configuration data is in the job documents, the
        job iteration count is recorded within a special "jobConfiguration" metric.

        This function identifies the set of job iterations for each benchmark
        configuration.

        TODO: this should allow targeting a specific OCP version, benchmark, and
        configuration. (Although I've yet to figure out how to compactly represent
        the configuration tuple in a query parameter.)
        """
        start = time.time()

        vees = sorted((await self.get_versions()).keys())
        # print(f"Discovered {vees}")

        benchmark_metrics = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        )
        config_key = defaultdict(dict)
        for ver in vees:
            bees = await self.get_benchmarks(ver)
            for benchmark, configurations in bees.items():
                # print(f"get_iterations {ver}: {benchmark}")
                # get the index -- and, for now, we only know what to make of
                # kube-burner benchmarks.
                idx = self.get_index(benchmark)
                if not idx or idx != "ripsaw-kube-burner":
                    continue

                for config in configurations:
                    uuids = sorted(config["uuids"])
                    # print(f"get_iterations {ver}/{benchmark}: {config}: {len(uuids)}")
                    query = {
                        "query": {
                            "bool": {"filter": [{"terms": {"uuid.keyword": uuids}}]}
                        },
                        "aggs": {
                            "jobIterations": {
                                "terms": {
                                    "field": "jobConfig.jobIterations",
                                    "size": 10000,
                                },
                                "aggs": {
                                    "uuids": {
                                        "terms": {
                                            "field": "uuid.keyword",
                                            "size": 10000,
                                        }
                                    }
                                },
                            },
                        },
                    }

                    response = await self.service.post(
                        indice=idx,
                        query=query,
                        size=0,
                    )
                    aggregate_uuids = []
                    for iterations in response["aggregations"]["jobIterations"][
                        "buckets"
                    ]:
                        try:
                            us = [u["key"] for u in iterations["uuids"]["buckets"]]
                            aggregate_uuids.extend(us)
                            ck = str(config["configuration"])
                            config_key[ck] = config["configuration"].json()
                            benchmark_metrics[ver][benchmark][ck][
                                iterations["key"]
                            ].extend(us)
                        except Exception as e:
                            print(
                                f"Exception in get_metrics: {e}:\n{benchmark}: {iterations}"
                            )
                            raise
        benchmark_report = {
            "config_key": config_key,
            "iterations": {
                v: {
                    b: {
                        c: {j: sorted(u) for j, u in vs.items()} for c, vs in cf.items()
                    }
                    for b, cf in d.items()
                }
                for v, d in benchmark_metrics.items()
            },
        }
        print(f"benchmark iterations: {time.time()-start:.3f} seconds")
        return benchmark_report

    async def metric_aggregation(self) -> dict[str, Any]:
        """Report aggregated metrics for each benchmark configuration.

        We can only compare benchmark metrics across the same configuration and job
        iteration count. While the configuration data is in the job documents, the
        job iteration count is recorded within a special "jobConfiguration" metric.
        """
        start = time.time()

        iterations = await self.get_iterations()
        breakdown = iterations["iterations"]
        metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for ver, benchmarks in breakdown.items():
            for benchmark, configs in benchmarks.items():
                for config, job_iterations in configs.items():
                    idx = self.get_index(benchmark)
                    if not idx or idx != "ripsaw-kube-burner":
                        continue
                    for i_count, uuids in job_iterations.items():
                        # print(f"KPI {i_count}: len(uuids) UUIDS")
                        filters = [{"terms": {"uuid.keyword": uuids}}]
                        filter = self.get_filter(benchmark)
                        if filter:
                            filters.extend(
                                [{"term": {k: v}} for k, v in filter.items()]
                            )
                        response = await self.service.post(
                            indice=idx,
                            size=MAX_PAGE,
                            query={
                                "query": {"bool": {"filter": filters}},
                                "sort": [{"timestamp": {"order": "asc"}}],
                                "aggs": {
                                    "stats": {
                                        "extended_stats": {
                                            "field": "P99",
                                        }
                                    },
                                },
                            },
                        )
                        values = [
                            {
                                "uuid": v["_source"]["uuid"],
                                "timestamp": v["_source"]["timestamp"],
                                "value": v["_source"]["P99"],
                            }
                            for v in response["hits"]["hits"]
                        ]
                        stats = response["aggregations"]["stats"]
                        stats = response["aggregations"]["stats"]
                        metrics[ver][benchmark][str(config)][i_count] = {
                            "values": values,
                            "stats": {
                                "count": stats["count"],
                                "min": stats["min"],
                                "max": stats["max"],
                                "avg": stats["avg"],
                                "std_dev": stats["std_deviation"],
                            },
                        }
        print(f"benchmark KPI report: {time.time()-start:.3f} seconds")
        return {"metrics": metrics, "config_key": iterations["config_key"]}


async def kpi_svc():
    """FastAPI Dependency to open & close ElasticService connections"""
    kpi = None
    try:
        kpi = KPI("ocp")
        yield kpi
    finally:
        if kpi:
            await kpi.close()


@router.get("/api/v1/ocp/kpi/versions")
async def versions(kpi: Annotated[KPI, Depends(kpi_svc)]) -> dict[str, list[str]]:
    """Return a list of OCP versions that have been tested.

    Args:
        kpi: An ElasticService instance and KPI cache structure
    """
    return await kpi.get_versions()


@router.get("/api/v1/ocp/kpi/benchmarks")
async def benchmarks(
    kpi: Annotated[KPI, Depends(kpi_svc)], versions: Optional[str] = None
) -> dict[str, Any]:
    """Return KPI data for a given OCP version.

    Args:
        kpi: An ElasticService instance and KPI cache structure
        version: The OCP version to get KPI data for.

    Returns:
        A hierarchical aggregation of KPI data for benchmark results for the
        given OCP version.
    """
    returns = {}
    vees = (
        (await kpi.get_versions()).keys() if versions is None else versions.split(",")
    )
    for v in vees:
        benchmarks = await kpi.get_benchmarks(v)
        returns[v] = benchmarks
    return returns


@router.get("/api/v1/ocp/kpi/breakdown")
async def foggy(kpi: Annotated[KPI, Depends(kpi_svc)]) -> dict[str, Any]:
    """Identify metric data indices for each benchmark."""
    return await kpi.get_iterations()


@router.get("/api/v1/ocp/kpi")
async def kpi(kpi: Annotated[KPI, Depends(kpi_svc)]) -> dict[str, Any]:
    """Identify metric data indices for each benchmark."""
    return await kpi.metric_aggregation()


async def search_metrics() -> dict[str, Any]:
    """Try to locate job UUIDs in the various prefixed indices.

    This ties each benchmark name to the set of kube-burner job names and
    metric names collected for each. (These are aggregated across OCP
    versions.)
    """
    vees = sorted((await get_versions()).keys())
    es = ElasticService(configpath="ocp.elasticsearch")

    benchmark_metrics = defaultdict(lambda: defaultdict(set))
    for ver in vees:
        bees = await get_benchmarks(ver)
        for benchmark, configurations in bees["benchmark_configurations"].items():
            uuids = []
            for config in configurations:
                uuids.extend(config["uuids"])
            uuids.sort()
            aggs = None
            idx = get_index(benchmark)
            if not idx:
                continue
            idx = "ospst-" + idx + "*"
            if idx.startswith("ospst-ripsaw-kube-burner"):
                aggs = {
                    "metricName": {
                        "terms": {
                            "field": "metricName.keyword",
                            "size": 10000,
                        },
                        "aggs": {
                            "jobName": {
                                "terms": {"field": "jobName.keyword", "size": 10000}
                            },
                            "jobIterations": {
                                "terms": {
                                    "field": "jobConfig.jobIterations",
                                    "size": 10000,
                                },
                            },
                        },
                    },
                }
            query = {
                "query": {"bool": {"filter": [{"terms": {"uuid.keyword": uuids}}]}},
            }
            if aggs:
                query["aggs"] = aggs
            response = await es.prev_es.search(
                index=idx,
                body=query,
                size=0,
            )
            if aggs:
                for metricname in response["aggregations"]["metricName"]["buckets"]:
                    try:
                        for jobiteration in metricname["jobIterations"]["buckets"]:
                            benchmark_metrics[benchmark][metricname["key"]].add(
                                jobiteration["key"]
                            )
                    except Exception as e:
                        print(
                            f"Exception in get_metrics: {e}:\n{metricname} ({sorted(metricname.keys())})"
                        )
                        raise
    await es.close()
    benchmark_report = {
        b: {j: sorted(v) for j, v in vs.items()} for b, vs in benchmark_metrics.items()
    }
    return benchmark_report
