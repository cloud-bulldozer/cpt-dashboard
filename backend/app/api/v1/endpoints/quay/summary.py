from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import time
from typing import Any, Optional

from app.api.v1.commons.constants import AGG_BUCKET_SIZE, MAX_PAGE
from app.api.v1.endpoints.ocp.summary import Benchmark, BenchmarkBase
from app.api.v1.endpoints.summary.summary_search import (
    PerfCiFingerprint,
    SearchBenchmark,
    SummarySearch,
)

"""Quay implementation of Summary class

AI assistance: Cursor is extremely helpful in generating suggesting code
snippets along the way. While most of this code is hand generated as the
relationships are tricky and difficult to describe to the AI, it's been
extremely helpful as an "over the shoulder assistant" to simplify routine
coding tasks.

Assisted-by: Cursor + claude-4-sonnet
"""


# TODO: Quay has metric data in two separate indices for their one
# benchmark. Can we make `index` handle a list?
BENCHMARK_INDEX: dict[str, Benchmark | None] = {
    "quay-load-test": Benchmark(
        index="quay-push-pull",
    ),
}


@dataclass(kw_only=True)
class QuayFingerprint(PerfCiFingerprint):
    hitSize: int = field(metadata={"str": "hs"})
    concurrency: int = field(metadata={"str": "c"})
    imagePushPulls: int = field(metadata={"str": "img"})


class QuaySummary(SummarySearch):

    def __init__(self, product: str, configpath: str = "quay.elasticsearch"):
        super().__init__(product, configpath, BENCHMARK_INDEX)

    def create_helper(self, benchmark: str) -> "BenchmarkBase":
        match self.get_index(benchmark):
            case "quay-push-pull":
                helper = PushPullBenchmark(self, benchmark)
            case "quay-vegeta-results":
                helper = VegetaBenchmark(self, benchmark)
            case _:
                raise ValueError(f"Unsupported benchmark: {benchmark}")
        return helper

    async def get_versions(self) -> dict[str, list[str]]:
        """Return a list of versions.

        Returns:
            The full version strings for each "short version" (e.g. "4.19").
        """
        start = time.time()
        filters = [{"match": {"jobStatus": "success"}}]
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
            {"match": {"jobStatus": "success"}},
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
                        "sources": QuayFingerprint.composite(),
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
                        "configuration": QuayFingerprint.parse(config["key"]),
                        "uuids": list(u),
                    }
                )
                benchmarks.add(b)
        print(
            f"discovered {version} benchmark hierarchy: {time.time()-start:3f} seconds"
        )
        return dict(by_benchmark)

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
                if not idx:
                    continue

                for config in configurations:
                    uuids = sorted(config["uuids"])
                    ck = config["configuration"].key()
                    config_key[ck] = config["configuration"].json()
                    try:
                        klass = self.get_helper(benchmark)
                    except ValueError as e:
                        print(f"Benchmark {benchmark} variants not supported: {e}")
                        benchmark_metrics[ver][benchmark][ck] = {}
                        continue
                    variants = await klass.get_iteration_variants(idx, uuids)
                    if not variants:
                        print(f"Benchmark {benchmark} variants not found")
                        benchmark_metrics[ver][benchmark][ck] = {}
                        continue
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
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        uuids: Optional[bool] = False,
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
                    b: {
                        c: {j: (u if uuids else len(u)) for j, u in vs.items()}
                        for c, vs in cf.items()
                    }
                    for b, cf in d.items()
                }
                for v, d in data["benchmarks"].items()
            },
        }
        return configs

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
                try:
                    klass = self.get_helper(benchmark)
                except ValueError as e:
                    print(f"Benchmark {benchmark} not supported: {e}")
                    continue
                benchmark_readiness = set()
                config_samples = defaultdict()
                for config, job_iterations in configs.items():
                    config_readiness = set()
                    iteration_samples = defaultdict()
                    for variation, uuids in job_iterations.items():
                        sample = await klass.process(ver, config, variation, uuids)
                        readiness = await klass.evaluate(sample)
                        config_readiness.add(readiness)
                        sample["readiness"] = readiness
                        iteration_samples[variation] = sample
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


class PushPullBenchmark(SearchBenchmark):

    async def get_iteration_variants(
        self, index: str, uuids: list[str]
    ) -> dict[str, list[str]]:
        """Report non-configuration discriminations.

        We don't disriminate below the "config" level for Quay, so we pass
        through all configuration UUIDs.
        """
        return {"n/a": uuids}

    async def process(
        self, version: str, config: str, variant: Any, uuids: list[str]
    ) -> dict[str, Any]:
        summary = self.summary
        filters = [{"terms": {"uuid.keyword": uuids}}]
        if summary.date_filter:
            filters.append(summary.date_filter)
        filter = summary.get_filter(self.benchmark)
        if filter:
            filters.extend([{"term": {k: v}} for k, v in filter.items()])
        response = await summary.service.post(
            indice=self.index,
            size=0,
            query={
                "query": {"bool": {"filter": filters}},
                "sort": [{"start_time": {"order": "asc"}}],
                "aggs": {
                    "stats": {
                        "extended_stats": {
                            "field": "elapsed_time",
                        }
                    },
                    "by_uuid": {
                        "terms": {
                            "field": "uuid.keyword",
                            "size": MAX_PAGE,
                        },
                        "aggs": {
                            "start_time": {
                                "min": {
                                    "field": "start_time",
                                }
                            },
                            "average": {
                                "avg": {
                                    "field": "elapsed_time",
                                }
                            },
                        },
                    },
                },
            },
        )
        x = []
        y = []
        values = []
        for hit in response["aggregations"]["by_uuid"]["buckets"]:
            uuid = hit["key"]
            average = hit["average"]["value"]

            # The "min" aggregation returns the timestamp in milliseconds as
            # a floating point number.
            start = datetime.fromtimestamp(hit["start_time"]["value"] / 1000.0)
            values.append(
                {
                    "uuid": uuid,
                    "timestamp": start,
                    "value": average,
                }
            )
        if len(values) < 1:
            print(f"no metrics found for {version} {self.benchmark} {config}: {uuids}")
        values.sort(key=lambda x: x["timestamp"])
        for value in values:
            x.append(value["timestamp"])
            y.append(value["value"])

        stats = response["aggregations"]["stats"]
        sample = {
            "values": values,
            "graph": {
                "x": x,
                "y": y,
                "name": f"{version} {self.benchmark} {config} {variant}",
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
        return sample

    async def evaluate(self, metric: dict[str, Any]) -> str:
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
        if len(metric["values"]) < 1:
            print(f"{self.benchmark} evaluating empty metric")
            return "warning"
        if metric["values"][-1]["value"] < metric["stats"]["avg"]:
            return "not ready"
        if metric["stats"]["std_dev"] > metric["stats"]["avg"] / 2:
            return "warning"
        return "ready"


class VegetaBenchmark(SearchBenchmark):

    async def get_iteration_variants(
        self, index: str, uuids: list[str]
    ) -> dict[str, list[str]]:
        return {"n/a": uuids}

    async def process(
        self, version: str, config: str, iter: int, uuids: list[str]
    ) -> dict[str, Any]:
        return {}

    async def evaluate(self, metric: dict[str, Any]) -> str:
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
        return "warning"
