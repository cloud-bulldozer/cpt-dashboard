from collections import defaultdict
from dataclasses import dataclass
import time
from typing import Any, Optional

from app.api.v1.commons.constants import AGG_BUCKET_SIZE, MAX_PAGE
from app.api.v1.endpoints.summary.summary_search import SummarySearch

"""OCP implementation of Summary class

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
            "metricName.keyword": "nodeLatencyQuantilesMeasurement",
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
            "quantileName.keyword": "VMIRunning",
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


class OcpSummary(SummarySearch):

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
        start = time.time()
        filters = [{"term": {"jobStatus.keyword": "success"}}]
        if self.date_filter:
            filters.append(self.date_filter)

        query = {
            "size": 0,
            "query": {"bool": {"filter": filters}},
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

        print(f"discovered {len(versions)} versions: {time.time()-start:3f} seconds")
        return {k: sorted(v) for k, v in versions.items()}

    async def get_benchmarks(self, version: str) -> dict[str, Any]:
        """Return a list of benchmarks run for a given product version.

        Args:
            version: The product version to get benchmarks for.

        Returns:
            A list of benchmarks and the configurations for which each is run.
        """
        filters = [
            {"term": {"jobStatus.keyword": "success"}},
        ]
        if self.date_filter:
            filters.append(self.date_filter)
        print("get_benchmarks", version)
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": filters,
                    "must": [{"query_string": {"query": f"ocpVersion:{version}*"}}],
                },
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
                        "size": AGG_BUCKET_SIZE,
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
        print(
            f"discovered {version} benchmark hierarchy: {time.time()-start:3f} seconds"
        )
        return dict(by_benchmark)

    async def get_iteration_variants(
        self, index: str, uuids: list[str]
    ) -> dict[str, list[str]]:
        filters = [
            {"terms": {"uuid.keyword": uuids}},
            {"term": {"metricName.keyword": "jobSummary"}},
        ]
        if self.date_filter:
            filters.append(self.date_filter)
        query = {
            "query": {"bool": {"filter": filters}},
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

        response = await self.service.post(indice=index, query=query, size=0)
        variants = defaultdict(list)
        for iterations in response["aggregations"]["jobIterations"]["buckets"]:
            us = sorted([u["key"] for u in iterations["uuids"]["buckets"]])
            variants[iterations["key"]].extend(us)
        return variants

    async def get_iterations(
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        configs: Optional[str] = None,
    ) -> dict[str, Any]:
        """Break down our benchmark configuration data by job iterations.

        We can only compare benchmark metrics across the same configuration and
        job iteration count. While the configuration data is in the job
        documents, the job iteration count is recorded within a special
        "jobConfiguration" metric.

        This function identifies the set of jobs that can be compared based on
        identical configuration and iteration count.

        TODO: this should allow targeting a specific OCP configuration.
        (Although I've yet to figure out how to compactly represent the
        configuration tuple in a query parameter.)
        """
        start = time.time()

        vees = sorted(
            (await self.get_versions()).keys()
            if not versions
            else self.break_list(versions)
        )

        benches = self.break_list(benchmarks) if benchmarks else None

        benchmark_metrics = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        )
        config_key = defaultdict(dict)
        for ver in vees:
            bees = await self.get_benchmarks(ver)
            for benchmark, configurations in bees.items():
                if benches and benchmark not in benches:
                    continue

                # get the index -- and, for now, we only know what to make of
                # kube-burner benchmarks.
                idx = self.get_index(benchmark)
                if not idx or idx != "ripsaw-kube-burner":
                    continue

                for config in configurations:
                    uuids = sorted(config["uuids"])
                    ck = str(config["configuration"])
                    config_key[ck] = config["configuration"].json()
                    variants = await self.get_iteration_variants(idx, uuids)
                    for iter, uuids in variants.items():
                        benchmark_metrics[ver][benchmark][ck][iter].extend(uuids)
        benchmark_report = {
            "config_key": config_key,
            "benchmarks": {
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

    async def get_configs(
        self, versions: Optional[str] = None, benchmarks: Optional[str] = None
    ) -> dict[str, Any]:
        """Return report the number of job iterations for each benchmark
        configuration.

        Args:
            versions: The OCP versions to get configurations for.
            benchmarks: The benchmarks to get configurations for.

        Returns:
            A report of the number of job iterations for each benchmark
            configuration.
        """
        data = await self.get_iterations(versions, benchmarks)
        configs = {
            "config_key": data["config_key"],
            "benchmarks": {
                v: {
                    b: {c: {j: len(u) for j, u in vs.items()} for c, vs in cf.items()}
                    for b, cf in d.items()
                }
                for v, d in data["benchmarks"].items()
            },
        }
        return configs

    async def metric_evaluation(self, metric: dict[str, Any]) -> str:
        """Evaluate a metric sample for the primary "readiness" KPI.

        This adds a "readiness" indicator to the metric sample, based on
        defined thresholds.

        This is a dummy implementation based on trivial and arbitrary rules.
        The benchmark is "not ready" if:

        * If the final value is below the average value, the metric is "not
          ready".

        The metric can also be "warning" state if:

        * If the standard deviation exceeds half the average value, the metric
          is "warning".

        Args:
            metric: A dictionary containing the metric sample.

        Returns:
            "ready", "warning", or "not ready"
        """
        if metric["values"][-1]["value"] < metric["stats"]["avg"]:
            return "not ready"
        if metric["stats"]["std_dev"] > metric["stats"]["avg"] / 2:
            return "warning"
        return "ready"

    def is_ready(self, readiness: set[str]) -> str:
        """Determine if the set of readiness indicators is "ready".

        Args:
            readiness: A set of readiness indicators.

        Returns:
            "ready", "warning", or "not ready"
        """
        return (
            "not ready"
            if "not ready" in readiness
            else "warning" if "warning" in readiness else "ready"
        )

    async def metric_aggregation(
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        configs: Optional[str] = None,
    ) -> dict[str, Any]:
        """Report aggregated metrics for each benchmark configuration.

        For each selected version, benchmark, configuration, report on the
        primary "readiness" KPI. The results include a list of individual
        timestamped values, a statistical summary, and a Plotly-formatted
        graph of the individual runs.

        Args:
            versions: Select only the named versions (comma-separated list)
            benchmarks: Select only the named benchmarks (comma-separated list)
            configs: Select only the named configurations (comma-separated list)

        """
        start = time.time()

        iterations = await self.get_iterations(versions, benchmarks)
        breakdown = iterations["benchmarks"]
        version_samples = defaultdict()
        product_readiness = set()
        for ver, benchmarks in breakdown.items():
            version_readiness = set()
            benchmark_samples = defaultdict()
            for benchmark, configs in benchmarks.items():
                benchmark_readiness = set()
                config_samples = defaultdict()
                for config, job_iterations in configs.items():
                    idx = self.get_index(benchmark)
                    if not idx or idx != "ripsaw-kube-burner":
                        continue
                    config_readiness = set()
                    iteration_samples = defaultdict()
                    for iter, uuids in job_iterations.items():
                        # print(f"KPI {i_count}: len(uuids) UUIDS")
                        filters = [{"terms": {"uuid.keyword": uuids}}]
                        if self.date_filter:
                            filters.append(self.date_filter)
                        filter = self.get_filter(benchmark)
                        if filter:
                            filters.extend(
                                [{"term": {k: v}} for k, v in filter.items()]
                            )
                        if benchmark == "virt-density":
                            print(f"filters: {filters}")
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
                        x = []
                        y = []
                        values = []
                        if benchmark == "virt-density":
                            print(f"response: {response}")
                        for hit in response["hits"]["hits"]:
                            v = hit["_source"]
                            values.append(
                                {
                                    "uuid": v["uuid"],
                                    "timestamp": v["timestamp"],
                                    "value": v["P99"],
                                }
                            )
                            x.append(v["timestamp"])
                            y.append(int(v["P99"]))
                        stats = response["aggregations"]["stats"]
                        sample = {
                            "values": values,
                            "graph": {
                                "x": x,
                                "y": y,
                                "name": f"{ver} {benchmark} {config} {iter:d}",
                                "type": "scatter",
                                "mode": "lines+markers",
                                "orientation": "v",
                            },
                            "stats": {
                                "min": stats["min"],
                                "max": stats["max"],
                                "avg": stats["avg"],
                                "std_dev": stats["std_deviation"],
                            },
                        }
                        readiness = await self.metric_evaluation(sample)
                        config_readiness.add(readiness)
                        sample["readiness"] = readiness
                        iteration_samples[iter] = sample
                    config_samples[config] = {
                        "iterations": iteration_samples,
                        "readiness": self.is_ready(config_readiness),
                    }
                    benchmark_readiness.update(config_readiness)
                benchmark_samples[benchmark] = {
                    "configurations": config_samples,
                    "readiness": self.is_ready(benchmark_readiness),
                }
                version_readiness.update(benchmark_readiness)
            version_samples[ver] = {
                "benchmarks": benchmark_samples,
                "readiness": self.is_ready(version_readiness),
            }
            product_readiness.update(version_readiness)
        print(f"benchmark KPI report: {time.time()-start:.3f} seconds")
        return {
            "config_key": iterations["config_key"],
            "versions": version_samples,
            "readiness": self.is_ready(product_readiness),
        }
