from abc import abstractmethod
from typing import Any, Optional

"""Information about product release KPIs.

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


class Summary:
    product: str
    configpath: str
    version: list[str]
    benchmarks: list[str]
    start_date: str | None
    end_date: str | None
    date_filter: dict[str, Any] | None
    service: Any = None

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
    ):
        self.product = product
        self.configpath = configpath
        self.start_date = None
        self.end_date = None
        self.date_filter = None
        self.service = None

    @abstractmethod
    def set_date_filter(self, start_date: str | None, end_date: str | None):
        """Set the date filter for the summary service."""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def close(self):
        """Close the summary service."""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def get_versions(self) -> dict[str, list[str]]:
        """Return a list of versions.

        This must be implemented by the subclass.

        Returns:
            The full version strings for each "short version" (e.g. "4.19").
        """
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def get_benchmarks(self, version: str) -> dict[str, Any]:
        """Return a list of benchmarks run for a given product version.

        This must be implemented by the subclass.

        Args:
            version: The product version to get benchmarks for.

        Returns:
            A list of benchmarks and the configurations for which each is run.
        """
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def get_iterations(
        self,
        versions: Optional[str] = None,
    ) -> dict[str, Any]:
        """Break down our benchmark configuration data.

        This must be implemented by the subclass.

        This function identifies the set of jobs that can be compared based on
        identical configuration and iteration count.
        """
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def get_configs(
        self, versions: Optional[str] = None, benchmarks: Optional[str] = None
    ) -> dict[str, Any]:
        """Return report the configurations for which each benchmar was run.

        This must be implemented by the subclass.

        Args:
            versions: The OCP versions to get configurations for.
            benchmarks: The benchmarks to get configurations for.
        """
        raise NotImplementedError("Not implemented")

    @abstractmethod
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

        This must be implemented by a subclass.

        Args:
            versions: Select only the named versions (comma-separated list)
            benchmarks: Select only the named benchmarks (comma-separated list)
            configs: Select only the named configurations (comma-separated list)

        """
        raise NotImplementedError("Not implemented")
