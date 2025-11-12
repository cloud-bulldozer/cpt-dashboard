from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.api.v1.endpoints.summary.summary import BaseFingerprint, BenchmarkBase, Summary
from app.services.search import ElasticService

"""CPT summary information for benchmarks using ElasticService.

This is a subclass of the Summary class targeted to products using the
ElasticService class to access OpenSearch data.

AI assistance: Cursor is extremely helpful in generating suggesting code
snippets along the way. While most of this code is hand generated as the
relationships are tricky and difficult to describe to the AI, it's been
extremely helpful as an "over the shoulder assistant" to simplify routine
coding tasks.

Assisted-by: Cursor + claude-4-sonnet
"""


@dataclass
class Benchmark:
    """Map each benchmark to an index and ElasticService filter.

    TODO: Some benchmarks have multiple indices, e.g. quay-load-test. We need
    to handle this case.
    """

    index: str
    filter: dict[str, str] | None = None


@dataclass
class PerfCiFingerprint(BaseFingerprint):
    """Extend the BaseFingerprint class with OCP-specific fields."""

    masterNodesType: str = field(metadata={"str": "mt", "key": True})
    masterNodesCount: int = field(metadata={"str": "mc"})
    workerNodesType: str = field(metadata={"str": "wt", "key": True})
    workerNodesCount: int = field(metadata={"str": "wc"})


class SummarySearch(Summary):
    """Summary subclass for benchmarks using ElasticService."""

    service: ElasticService = None
    date_filter: dict[str, Any] | None
    benchmarks: dict[str, Benchmark]
    benchmark_helper: dict[str, "BenchmarkBase"]

    def __init__(
        self,
        product: str,
        configpath: str = "ocp.elasticsearch",
        benchmarks: dict[str, Benchmark] | None = None,
    ):
        super().__init__(product, configpath)
        print(f"opening ElasticService ({configpath})")
        self.service = ElasticService(configpath)
        self.date_filter = None
        self.benchmarks = benchmarks or {}
        self.benchmark_helper = {}

    def get_index(self, benchmark: str) -> str | None:
        """Get the index associated with a benchmark."""
        b = self.benchmarks.get(benchmark)
        return b.index if b else None

    def get_filter(self, benchmark: str) -> dict[str, str] | None:
        """Get the filter associated with a benchmark."""
        b = self.benchmarks.get(benchmark)
        return b.filter if b else None

    def get_helper(self, benchmark: str) -> "BenchmarkBase":
        """Get a benchmark helper class instance for a benchmark."""
        helper = self.benchmark_helper.get(benchmark)
        if not helper:
            print(f"creating helper for benchmark {benchmark}")
            helper = self.create_helper(benchmark)
            self.benchmark_helper[benchmark] = helper
        return helper

    @abstractmethod
    def create_helper(self, benchmark: str) -> "BenchmarkBase":
        """Create an instance of the helper class for a benchmark."""
        raise NotImplementedError("Subclasses must implement this method")

    def set_date_filter(self, start_date: str | None, end_date: str | None):
        """Create a date filter dict for a given start and end date."""
        if start_date or end_date:
            self.end_date = end_date
            self.date_filter = None
            range = {"format": "yyyy-MM-dd"}
            if start_date:
                range["gte"] = start_date
            if end_date:
                range["lte"] = end_date
            self.date_filter = {
                "range": {
                    "timestamp": range,
                }
            }
        else:
            self.date_filter = None

    @abstractmethod
    async def close(self):
        """Close the summary service."""
        print(f"closing {type(self.service).__name__}")
        await self.service.close()


class SearchBenchmark(BenchmarkBase):
    """BenchmarkBase subclass for benchmarks using ElasticService."""

    summary: Summary
    benchmark: str
    index: str | None = None

    def __init__(self, summary: Summary, benchmark: str):
        """Initialize the SearchBenchmark instance."""
        super().__init__(summary, benchmark)
        self.index = summary.get_index(benchmark)
