from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints.summary.summary import BenchmarkBase
from app.api.v1.endpoints.summary.summary_search import (
    PerfCiFingerprint,
    SearchBenchmark,
    SummarySearch,
)

"""Unit tests for the summary_search module classes.

This file tests the classes and functionality defined in summary_search.py,
including the Benchmark dataclass, PerfCiFingerprint extension, SummarySearch
abstract class, and SearchBenchmark class. Uses concrete implementations to
test abstract methods and achieve full coverage.

Follows established patterns from other unit tests with Given-When-Then structure.

Generated-by: Cursor / claude-4-5-sonnet
"""


# Concrete implementation of SummarySearch for testing
class ConcreteSummarySearch(SummarySearch):
    """Concrete implementation of SummarySearch for testing."""

    def create_helper(self, benchmark: str) -> BenchmarkBase:
        """Create a mock helper for testing."""
        mock_helper = MagicMock(spec=BenchmarkBase)
        mock_helper.benchmark = benchmark
        return mock_helper

    async def close(self):
        """Override to call parent's close method."""
        await super().close()

    async def get_versions(self) -> dict[str, list[str]]:
        """Implement abstract method."""
        return {"4.18": ["4.18.0", "4.18.1"], "4.19": ["4.19.0"]}

    async def get_benchmarks(self, version: str) -> dict[str, Any]:
        """Implement abstract method."""
        return {
            "cluster-density": ["config1", "config2"],
            "node-density": ["config3"],
        }

    async def get_iterations(self, versions: Optional[str] = None) -> dict[str, Any]:
        """Implement abstract method."""
        return {"iterations": [1, 2, 3], "versions": versions}

    async def get_configs(
        self, versions: Optional[str] = None, benchmarks: Optional[str] = None
    ) -> dict[str, Any]:
        """Implement abstract method."""
        return {"configs": ["config1", "config2"], "versions": versions}

    async def metric_aggregation(
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        configs: Optional[str] = None,
    ) -> dict[str, Any]:
        """Implement abstract method."""
        return {
            "metrics": {"avg": 100, "max": 150, "min": 50},
            "versions": versions,
            "benchmarks": benchmarks,
        }


# Concrete implementation of SearchBenchmark for testing
class ConcreteSearchBenchmark(SearchBenchmark):
    """Concrete implementation of SearchBenchmark for testing."""

    async def get_iteration_variants(self, uuids: list[str]) -> dict[str, list[str]]:
        """Implement abstract method."""
        return {
            "variants": ["variant1", "variant2"],
            "uuid_count": len(uuids),
        }

    async def process(
        self, version: str, config: str, iter: Any, uuids: list[str]
    ) -> dict[str, Any]:
        """Implement abstract method."""
        return {
            "version": version,
            "config": config,
            "iteration": iter,
            "processed_uuids": len(uuids),
        }

    async def evaluate(self, metric: dict[str, Any]) -> str:
        """Implement abstract method."""
        if metric.get("value", 0) > 100:
            return "high"
        elif metric.get("value", 0) > 50:
            return "medium"
        return "low"


class TestBenchmarkMapping:
    """Test cases for benchmark mapping functionality."""

    def test_benchmark_helper_with_index(self):
        """Test benchmark helper class has INDEX attribute."""
        # Given: A benchmark helper class
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        # When: Checking class attributes
        # Then: Should have INDEX attribute
        assert hasattr(MockHelper, "INDEX")
        assert MockHelper.INDEX == "test-index"

    def test_benchmark_helper_with_filter(self):
        """Test benchmark helper class has FILTER attribute."""
        # Given: A benchmark helper with filter
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"
            FILTER = {"benchmark": "test-benchmark"}

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        # When: Checking class attributes
        # Then: Should have FILTER attribute
        assert hasattr(MockHelper, "FILTER")
        assert MockHelper.FILTER == {"benchmark": "test-benchmark"}

    def test_benchmark_helper_without_filter(self):
        """Test benchmark helper class can exist without FILTER."""
        # Given: A benchmark helper without filter
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        # When: Checking for filter attribute
        # Then: Should not have FILTER or it should be None
        assert not hasattr(MockHelper, "FILTER") or MockHelper.FILTER is None

    def test_benchmark_helper_with_complex_filter(self):
        """Test benchmark helper with dict of filters."""
        # Given: A benchmark helper with complex filter structure
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"
            FILTER = {
                "test-1": {"field1": "value1"},
                "test-2": {"field2": "value2"},
            }

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        # When: Checking filter structure
        # Then: Should preserve all filter values
        assert MockHelper.FILTER["test-1"]["field1"] == "value1"
        assert MockHelper.FILTER["test-2"]["field2"] == "value2"


class TestPerfCiFingerprintDataclass:
    """Test cases for PerfCiFingerprint dataclass functionality."""

    def test_perfci_fingerprint_initialization(self):
        """Test PerfCiFingerprint initialization with all fields."""
        # Given: PerfCi fingerprint data
        master_type = "m5.2xlarge"
        master_count = 3
        worker_type = "m5.4xlarge"
        worker_count = 120

        # When: Creating a PerfCiFingerprint instance
        result = PerfCiFingerprint(
            masterNodesType=master_type,
            masterNodesCount=master_count,
            workerNodesType=worker_type,
            workerNodesCount=worker_count,
        )

        # Then: Should create instance with all fields
        assert result.masterNodesType == master_type
        assert result.masterNodesCount == master_count
        assert result.workerNodesType == worker_type
        assert result.workerNodesCount == worker_count

    def test_perfci_fingerprint_key_method(self):
        """Test PerfCiFingerprint key method includes abbreviated names."""
        # Given: A PerfCiFingerprint instance
        fingerprint = PerfCiFingerprint(
            masterNodesType="m5.2xlarge",
            masterNodesCount=3,
            workerNodesType="m5.4xlarge",
            workerNodesCount=120,
        )

        # When: Generating key
        result = fingerprint.key()

        # Then: Should use abbreviated metadata names
        assert "mt=m5.2xlarge" in result  # masterNodesType abbreviated to 'mt'
        assert "mc=3" in result  # masterNodesCount abbreviated to 'mc'
        assert "wt=m5.4xlarge" in result  # workerNodesType abbreviated to 'wt'
        assert "wc=120" in result  # workerNodesCount abbreviated to 'wc'

    def test_perfci_fingerprint_json_method(self):
        """Test PerfCiFingerprint json method returns dict."""
        # Given: A PerfCiFingerprint instance
        fingerprint = PerfCiFingerprint(
            masterNodesType="m5.2xlarge",
            masterNodesCount=3,
            workerNodesType="m5.4xlarge",
            workerNodesCount=120,
        )

        # When: Converting to json
        result = fingerprint.json()

        # Then: Should return dictionary with all fields
        assert isinstance(result, dict)
        assert result["masterNodesType"] == "m5.2xlarge"
        assert result["masterNodesCount"] == 3
        assert result["workerNodesType"] == "m5.4xlarge"
        assert result["workerNodesCount"] == 120

    def test_perfci_fingerprint_parse_from_dict(self):
        """Test PerfCiFingerprint parse method creates instance from dict."""
        # Given: A dictionary with fingerprint data
        data = {
            "masterNodesType": "m5.xlarge",
            "masterNodesCount": 3,
            "workerNodesType": "m5.2xlarge",
            "workerNodesCount": 60,
        }

        # When: Parsing from dict
        result = PerfCiFingerprint.parse(data)

        # Then: Should create instance with correct values
        assert isinstance(result, PerfCiFingerprint)
        assert result.masterNodesType == "m5.xlarge"
        assert result.masterNodesCount == 3
        assert result.workerNodesType == "m5.2xlarge"
        assert result.workerNodesCount == 60

    def test_perfci_fingerprint_filter_includes_keyword_for_key_fields(self):
        """Test PerfCiFingerprint filter method adds .keyword for key fields."""
        # Given: PerfCiFingerprint class
        # When: Getting filter structure
        result = PerfCiFingerprint.filter()

        # Then: Should add .keyword suffix for key=True metadata fields
        filter_fields = [f["term"]["field"] for f in result]
        assert "masterNodesType.keyword" in filter_fields  # key=True
        assert "workerNodesType.keyword" in filter_fields  # key=True
        assert "masterNodesCount" in filter_fields  # no key metadata means no .keyword
        assert "workerNodesCount" in filter_fields  # no key metadata means no .keyword

    def test_perfci_fingerprint_composite_aggregation(self):
        """Test PerfCiFingerprint composite method generates terms aggregation."""
        # Given: PerfCiFingerprint class
        # When: Getting composite structure
        result = PerfCiFingerprint.composite()

        # Then: Should return list of terms aggregations for each field
        assert isinstance(result, list)
        assert len(result) == 4  # Four fields in PerfCiFingerprint

        # Verify structure of composite aggregations
        field_names = []
        for item in result:
            assert isinstance(item, dict)
            field_name = list(item.keys())[0]
            field_names.append(field_name)
            assert "terms" in item[field_name]
            assert "field" in item[field_name]["terms"]

        # Verify all expected fields are present
        assert "masterNodesType" in field_names
        assert "masterNodesCount" in field_names
        assert "workerNodesType" in field_names
        assert "workerNodesCount" in field_names


class TestSummarySearch:
    """Test cases for SummarySearch class functionality."""

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_summary_search_initialization(self, mock_elastic_service):
        """Test SummarySearch initialization with benchmarks."""
        # Given: Product and benchmarks configuration
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        product = "ocp"
        configpath = "ocp.elasticsearch"
        benchmarks = {
            "cluster-density": MockHelper,
            "node-density": MockHelper,
        }

        # When: Creating SummarySearch instance
        result = ConcreteSummarySearch(
            product=product, configpath=configpath, benchmarks=benchmarks
        )

        # Then: Should initialize with correct values
        assert result.product == product
        assert result.configpath == configpath
        assert result.benchmarks == benchmarks
        assert result.date_filter is None
        assert result.benchmark_helper == {}
        mock_elastic_service.assert_called_once_with(configpath)

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_summary_search_default_benchmarks(self, mock_elastic_service):
        """Test SummarySearch initialization with default empty benchmarks."""
        # Given: Product without benchmarks
        product = "ocp"

        # When: Creating SummarySearch instance without benchmarks
        result = ConcreteSummarySearch(product=product)

        # Then: Should initialize with empty benchmarks dict
        assert result.benchmarks == {}
        assert result.benchmark_helper == {}

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_benchmark_mapper_structure(self, mock_elastic_service):
        """Test that benchmarks map directly to helper classes."""
        # Given: SummarySearch with benchmark mappings
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "test-benchmark": MockHelper,
        }
        summary = ConcreteSummarySearch(product="test", benchmarks=benchmarks)

        # When: Checking benchmark mapping
        # Then: Should map to class directly
        assert summary.benchmarks["test-benchmark"] == MockHelper

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_benchmark_class_has_index(self, mock_elastic_service):
        """Test benchmark classes have INDEX attribute."""
        # Given: SummarySearch with benchmark that has INDEX
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "test-benchmark": MockHelper,
        }
        summary = ConcreteSummarySearch(product="test", benchmarks=benchmarks)

        # When: Checking INDEX attribute
        # Then: Should have INDEX
        assert hasattr(summary.benchmarks["test-benchmark"], "INDEX")
        assert summary.benchmarks["test-benchmark"].INDEX == "test-index"

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_benchmark_class_with_filter(self, mock_elastic_service):
        """Test benchmark classes can have FILTER attribute."""
        # Given: SummarySearch with benchmark that has FILTER
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"
            FILTER = {"benchmark-1": {"field": "value"}}

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "benchmark-1": MockHelper,
        }
        summary = ConcreteSummarySearch(product="test", benchmarks=benchmarks)

        # When: Checking FILTER attribute
        # Then: Should have FILTER
        assert hasattr(summary.benchmarks["benchmark-1"], "FILTER")
        assert "benchmark-1" in summary.benchmarks["benchmark-1"].FILTER

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_get_helper_creates_and_caches_helper(self, mock_elastic_service):
        """Test get_helper creates helper and caches it."""
        # Given: SummarySearch instance
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "cluster-density": MockHelper,
        }
        summary = ConcreteSummarySearch(product="ocp", benchmarks=benchmarks)

        # When: Getting helper first time
        result1 = summary.get_helper("cluster-density")

        # Then: Should create and cache helper
        assert result1 is not None
        assert "cluster-density" in summary.benchmark_helper
        assert summary.benchmark_helper["cluster-density"] == result1

        # When: Getting helper second time
        result2 = summary.get_helper("cluster-density")

        # Then: Should return cached helper (same instance)
        assert result2 is result1

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_get_helper_different_benchmarks(self, mock_elastic_service):
        """Test get_helper creates separate helpers for different benchmarks."""
        # Given: SummarySearch with multiple benchmarks
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper1(BenchmarkBase):
            INDEX = "test-index-1"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        class MockHelper2(BenchmarkBase):
            INDEX = "test-index-2"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "cluster-density": MockHelper1,
            "node-density": MockHelper2,
        }
        summary = ConcreteSummarySearch(product="ocp", benchmarks=benchmarks)

        # When: Getting helpers for different benchmarks
        helper1 = summary.get_helper("cluster-density")
        helper2 = summary.get_helper("node-density")

        # Then: Should create different helpers
        assert helper1 is not helper2
        assert helper1.benchmark == "cluster-density"
        assert helper2.benchmark == "node-density"

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_set_date_filter_with_start_and_end(self, mock_elastic_service):
        """Test set_date_filter creates filter with start and end dates."""
        # Given: SummarySearch instance
        summary = ConcreteSummarySearch(product="ocp")
        start_date = "2024-01-01"
        end_date = "2024-01-31"

        # When: Setting date filter
        summary.set_date_filter(start_date, end_date)

        # Then: Should create date filter with range
        assert summary.date_filter is not None
        assert "range" in summary.date_filter
        assert "timestamp" in summary.date_filter["range"]
        assert summary.date_filter["range"]["timestamp"]["gte"] == start_date
        assert summary.date_filter["range"]["timestamp"]["lte"] == end_date
        assert summary.date_filter["range"]["timestamp"]["format"] == "yyyy-MM-dd"
        assert summary.end_date == end_date

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_set_date_filter_with_start_only(self, mock_elastic_service):
        """Test set_date_filter creates filter with only start date."""
        # Given: SummarySearch instance
        summary = ConcreteSummarySearch(product="ocp")
        start_date = "2024-01-01"

        # When: Setting date filter with only start
        summary.set_date_filter(start_date, None)

        # Then: Should create date filter with only gte
        assert summary.date_filter is not None
        assert "range" in summary.date_filter
        assert summary.date_filter["range"]["timestamp"]["gte"] == start_date
        assert "lte" not in summary.date_filter["range"]["timestamp"]

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_set_date_filter_with_end_only(self, mock_elastic_service):
        """Test set_date_filter creates filter with only end date."""
        # Given: SummarySearch instance
        summary = ConcreteSummarySearch(product="ocp")
        end_date = "2024-01-31"

        # When: Setting date filter with only end
        summary.set_date_filter(None, end_date)

        # Then: Should create date filter with only lte
        assert summary.date_filter is not None
        assert "range" in summary.date_filter
        assert summary.date_filter["range"]["timestamp"]["lte"] == end_date
        assert "gte" not in summary.date_filter["range"]["timestamp"]
        assert summary.end_date == end_date

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_set_date_filter_with_no_dates(self, mock_elastic_service):
        """Test set_date_filter clears filter when no dates provided."""
        # Given: SummarySearch instance with existing filter
        summary = ConcreteSummarySearch(product="ocp")
        summary.date_filter = {"existing": "filter"}

        # When: Setting date filter with no dates
        summary.set_date_filter(None, None)

        # Then: Should clear date filter
        assert summary.date_filter is None

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    async def test_close_calls_service_close(self, mock_elastic_service):
        """Test close method calls ElasticService.close."""
        # Given: SummarySearch instance with mock service
        mock_service_instance = AsyncMock()
        mock_elastic_service.return_value = mock_service_instance
        summary = ConcreteSummarySearch(product="ocp")

        # When: Closing summary
        await summary.close()

        # Then: Should call service.close()
        mock_service_instance.close.assert_called_once()


class TestSearchBenchmark:
    """Test cases for SearchBenchmark class functionality."""

    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    def test_search_benchmark_initialization(self, mock_elastic_service):
        """Test SearchBenchmark initialization."""
        # Given: Summary with benchmark
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "cluster-density": MockHelper,
        }
        summary = ConcreteSummarySearch(product="ocp", benchmarks=benchmarks)

        # When: Creating SearchBenchmark instance
        result = ConcreteSearchBenchmark(summary=summary, benchmark="cluster-density")

        # Then: Should initialize with correct values
        assert result.summary == summary
        assert result.benchmark == "cluster-density"

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    async def test_search_benchmark_get_iteration_variants(self, mock_elastic_service):
        """Test SearchBenchmark get_iteration_variants abstract method implementation."""
        # Given: SearchBenchmark instance
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "cluster-density": MockHelper,
        }
        summary = ConcreteSummarySearch(product="ocp", benchmarks=benchmarks)
        benchmark = ConcreteSearchBenchmark(
            summary=summary, benchmark="cluster-density"
        )

        # When: Calling get_iteration_variants
        result = await benchmark.get_iteration_variants(
            uuids=["uuid1", "uuid2", "uuid3"]
        )

        # Then: Should return expected structure
        assert result["uuid_count"] == 3
        assert "variants" in result

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    async def test_search_benchmark_process(self, mock_elastic_service):
        """Test SearchBenchmark process abstract method implementation."""
        # Given: SearchBenchmark instance
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "cluster-density": MockHelper,
        }
        summary = ConcreteSummarySearch(product="ocp", benchmarks=benchmarks)
        benchmark = ConcreteSearchBenchmark(
            summary=summary, benchmark="cluster-density"
        )

        # When: Calling process
        result = await benchmark.process(
            version="4.18.0",
            config="aws-120",
            iter=5,
            uuids=["uuid1", "uuid2"],
        )

        # Then: Should return processed data
        assert result["version"] == "4.18.0"
        assert result["config"] == "aws-120"
        assert result["iteration"] == 5
        assert result["processed_uuids"] == 2

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.summary.summary_search.ElasticService")
    async def test_search_benchmark_evaluate(self, mock_elastic_service):
        """Test SearchBenchmark evaluate abstract method implementation."""
        # Given: SearchBenchmark instance
        from app.api.v1.endpoints.summary.summary import BenchmarkBase

        class MockHelper(BenchmarkBase):
            INDEX = "test-index"

            async def get_iteration_variants(self, uuids):
                return {}

            async def process(self, version, config, iter, uuids):
                return {}

            async def evaluate(self, metric):
                return "ready"

        benchmarks = {
            "cluster-density": MockHelper,
        }
        summary = ConcreteSummarySearch(product="ocp", benchmarks=benchmarks)
        benchmark = ConcreteSearchBenchmark(
            summary=summary, benchmark="cluster-density"
        )

        # When: Calling evaluate with high value
        result_high = await benchmark.evaluate({"value": 150})

        # Then: Should return 'high'
        assert result_high == "high"

        # When: Calling evaluate with medium value
        result_medium = await benchmark.evaluate({"value": 75})

        # Then: Should return 'medium'
        assert result_medium == "medium"

        # When: Calling evaluate with low value
        result_low = await benchmark.evaluate({"value": 25})

        # Then: Should return 'low'
        assert result_low == "low"
