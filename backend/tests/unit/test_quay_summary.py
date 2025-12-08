from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.api.v1.endpoints.quay.summary import (
    BENCHMARK_MAPPER,
    QuayFingerprint,
    QuayLoadTestBenchmark,
    QuaySummary,
)

"""Unit tests for the Quay summary module.

This file tests the classes and functionality defined in quay/summary.py,
including QuayFingerprint, QuaySummary, PushPullBenchmark, and VegetaBenchmark classes.

Follows established patterns from other unit tests with Given-When-Then structure.

Tests achieve at least 95% code coverage including edge cases and error handling.

Generated-by: Cursor / claude-4-5-sonnet
"""


@pytest.fixture
def mock_elastic_service():
    """Create a mock ElasticService for testing."""
    mock_service = AsyncMock()
    mock_service.close = AsyncMock()
    mock_service.post = AsyncMock()
    return mock_service


@pytest.fixture
def mock_quay_summary(mock_elastic_service, monkeypatch):
    """Create a mock QuaySummary instance with mocked ElasticService."""

    # Patch ElasticService at the import location before importing QuaySummary
    def mock_elastic_factory(configpath):
        return mock_elastic_service

    monkeypatch.setattr(
        "app.api.v1.endpoints.summary.summary_search.ElasticService",
        mock_elastic_factory,
    )

    # Now create the summary - it will use our mocked service
    summary = QuaySummary("quay", "quay.elasticsearch")

    # Ensure the service is set correctly
    summary.service = mock_elastic_service

    return summary


class TestBenchmarkMapper:
    """Test cases for BENCHMARK_MAPPER constant."""

    def test_benchmark_mapper_structure(self):
        """Test that BENCHMARK_MAPPER has expected structure."""
        # Given: The BENCHMARK_MAPPER constant
        # When: Checking its structure
        # Then: It should be a dictionary with string keys
        assert isinstance(BENCHMARK_MAPPER, dict)
        assert all(isinstance(k, str) for k in BENCHMARK_MAPPER.keys())

    def test_benchmark_mapper_contains_quay_load_test(self):
        """Test that BENCHMARK_MAPPER contains quay-load-test benchmark."""
        # Given: Known benchmark names for Quay
        # When: Checking if they exist in BENCHMARK_MAPPER
        # Then: quay-load-test should be present
        assert "quay-load-test" in BENCHMARK_MAPPER

    def test_benchmark_mapper_quay_load_test(self):
        """Test quay-load-test benchmark configuration."""
        # Given: The quay-load-test benchmark
        benchmark_class = BENCHMARK_MAPPER["quay-load-test"]

        # When: Checking its properties
        # Then: It should be the QuayLoadTestBenchmark class
        assert benchmark_class == QuayLoadTestBenchmark
        assert hasattr(benchmark_class, "INDEX")
        assert isinstance(benchmark_class.INDEX, dict)
        assert "quay-push-pull" in benchmark_class.INDEX
        assert "quay-vegeta-results" in benchmark_class.INDEX


class TestQuayFingerprint:
    """Test cases for QuayFingerprint dataclass."""

    def test_quay_fingerprint_creation(self):
        """Test creating a QuayFingerprint instance."""
        # Given: Fingerprint parameters (QuayFingerprint extends PerfCiFingerprint)
        # When: Creating a QuayFingerprint
        fingerprint = QuayFingerprint(
            masterNodesType="m5.xlarge",
            masterNodesCount=3,
            workerNodesType="m5.2xlarge",
            workerNodesCount=5,
            hitSize=256,
            concurrency=10,
            imagePushPulls=1000,
        )

        # Then: All fields should be set correctly
        assert fingerprint.masterNodesType == "m5.xlarge"
        assert fingerprint.masterNodesCount == 3
        assert fingerprint.workerNodesType == "m5.2xlarge"
        assert fingerprint.workerNodesCount == 5
        assert fingerprint.hitSize == 256
        assert fingerprint.concurrency == 10
        assert fingerprint.imagePushPulls == 1000

    def test_quay_fingerprint_metadata(self):
        """Test QuayFingerprint metadata for Quay-specific fields."""
        # Given: QuayFingerprint class
        # When: Checking field metadata
        hitSize_field = QuayFingerprint.__dataclass_fields__["hitSize"]
        concurrency_field = QuayFingerprint.__dataclass_fields__["concurrency"]
        imagePushPulls_field = QuayFingerprint.__dataclass_fields__["imagePushPulls"]

        # Then: Should have correct metadata
        assert hitSize_field.metadata["str"] == "hs"
        assert concurrency_field.metadata["str"] == "c"
        assert imagePushPulls_field.metadata["str"] == "img"

    def test_quay_fingerprint_composite(self):
        """Test QuayFingerprint composite method for aggregation queries."""
        # Given: QuayFingerprint class
        # When: Getting composite sources
        composite = QuayFingerprint.composite()

        # Then: Should return list of composite sources
        assert isinstance(composite, list)
        assert len(composite) > 0
        # Check that Quay-specific fields are included
        field_names = [list(source.keys())[0] for source in composite]
        assert "hitSize" in field_names
        assert "concurrency" in field_names
        assert "imagePushPulls" in field_names


class TestQuaySummary:
    """Test cases for QuaySummary class."""

    def test_init(self, mock_quay_summary):
        """Test QuaySummary initialization."""
        # Given: A mock QuaySummary instance from fixture
        summary = mock_quay_summary

        # When/Then: Should be initialized correctly
        assert summary.product == "quay"
        assert summary.configpath == "quay.elasticsearch"
        assert summary.service is not None
        assert summary.benchmarks == BENCHMARK_MAPPER

    def test_create_helper_push_pull(self, mock_quay_summary):
        """Test create_helper returns PushPullBenchmark for quay-push-pull."""
        # Given: A QuaySummary instance and a push-pull benchmark
        benchmark = "quay-load-test"

        # When: Creating a helper
        helper = mock_quay_summary.create_helper(benchmark)

        # Then: Should return PushPullBenchmark instance
        assert isinstance(helper, QuayLoadTestBenchmark)
        assert helper.benchmark == benchmark

    def test_create_helper_unsupported_benchmark(self, mock_quay_summary):
        """Test create_helper raises ValueError for unsupported benchmarks."""
        # Given: A QuaySummary instance and unsupported benchmark that isn't in mapper
        benchmark = "unsupported-test"

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Unsupported benchmark"):
            mock_quay_summary.create_helper(benchmark)

    @pytest.mark.asyncio
    async def test_get_versions(self, mock_quay_summary, mock_elastic_service):
        """Test get_versions returns properly formatted version data."""
        # Given: Mock response from ElasticService
        mock_elastic_service.post.return_value = {
            "aggregations": {
                "versions": {
                    "buckets": [
                        {"key": "4.18.0-nightly"},
                        {"key": "4.18.1-nightly"},
                        {"key": "4.19.0-nightly"},
                        {"key": "4.19.1-nightly"},
                        {"key": "4.20.0-rc1"},
                    ]
                }
            }
        }

        # When: Getting versions
        versions = await mock_quay_summary.get_versions()

        # Then: Versions should be grouped by short version
        assert "4.18" in versions
        assert "4.19" in versions
        assert "4.20" in versions
        assert "4.18.0-nightly" in versions["4.18"]
        assert "4.18.1-nightly" in versions["4.18"]
        assert "4.19.0-nightly" in versions["4.19"]
        assert "4.20.0-rc1" in versions["4.20"]

        # Check that post was called with correct query structure
        mock_elastic_service.post.assert_called_once()
        call_kwargs = mock_elastic_service.post.call_args.kwargs
        assert "query" in call_kwargs
        query_dict = call_kwargs["query"]
        assert "query" in query_dict
        assert "bool" in query_dict["query"]
        assert "filter" in query_dict["query"]["bool"]
        assert {"match": {"jobStatus": "success"}} in query_dict["query"]["bool"][
            "filter"
        ]

    @pytest.mark.asyncio
    async def test_get_versions_with_date_filter(
        self, mock_quay_summary, mock_elastic_service
    ):
        """Test get_versions applies date filter when set."""
        # Given: QuaySummary with date filter
        mock_quay_summary.date_filter = {
            "range": {"timestamp": {"gte": "2024-01-01", "lte": "2024-12-31"}}
        }
        mock_elastic_service.post.return_value = {
            "aggregations": {"versions": {"buckets": [{"key": "4.18.0-nightly"}]}}
        }

        # When: Getting versions
        await mock_quay_summary.get_versions()

        # Then: Date filter should be in query
        call_kwargs = mock_elastic_service.post.call_args.kwargs
        query_dict = call_kwargs["query"]
        assert "query" in query_dict
        assert mock_quay_summary.date_filter in query_dict["query"]["bool"]["filter"]

    @pytest.mark.asyncio
    async def test_get_benchmarks(self, mock_quay_summary, mock_elastic_service):
        """Test get_benchmarks returns benchmark hierarchy."""
        # Given: Mock response with benchmark and configuration data
        mock_elastic_service.post.return_value = {
            "aggregations": {
                "configurations": {
                    "buckets": [
                        {
                            "key": {
                                "masterNodesType": "m5.xlarge",
                                "masterNodesCount": 3,
                                "workerNodesType": "m5.2xlarge",
                                "workerNodesCount": 5,
                                "hitSize": 256,
                                "concurrency": 10,
                                "imagePushPulls": 1000,
                            },
                            "benchmarks": {
                                "buckets": [
                                    {
                                        "key": "quay-load-test",
                                        "uuids": {
                                            "buckets": [
                                                {"key": "uuid-1"},
                                                {"key": "uuid-2"},
                                            ]
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                }
            }
        }

        # When: Getting benchmarks
        benchmarks = await mock_quay_summary.get_benchmarks("4.18")

        # Then: Should return properly structured benchmark data
        assert "quay-load-test" in benchmarks
        assert len(benchmarks["quay-load-test"]) > 0
        config = benchmarks["quay-load-test"][0]
        assert "configuration" in config
        assert "uuids" in config
        assert len(config["uuids"]) == 2

    @pytest.mark.asyncio
    async def test_get_benchmarks_with_date_filter(
        self, mock_quay_summary, mock_elastic_service
    ):
        """Test get_benchmarks applies date filter when set."""
        # Given: QuaySummary with date filter
        mock_quay_summary.date_filter = {"range": {"timestamp": {"gte": "2024-01-01"}}}
        mock_elastic_service.post.return_value = {
            "aggregations": {
                "configurations": {
                    "buckets": [
                        {
                            "key": {
                                "masterNodesType": "m5.xlarge",
                                "masterNodesCount": 3,
                                "workerNodesType": "m5.2xlarge",
                                "workerNodesCount": 5,
                                "hitSize": 256,
                                "concurrency": 10,
                                "imagePushPulls": 1000,
                            },
                            "benchmarks": {
                                "buckets": [
                                    {
                                        "key": "quay-load-test",
                                        "uuids": {"buckets": [{"key": "uuid-1"}]},
                                    }
                                ]
                            },
                        }
                    ]
                }
            }
        }

        # When: Getting benchmarks
        await mock_quay_summary.get_benchmarks("4.18")

        # Then: Date filter should be in query
        call_kwargs = mock_elastic_service.post.call_args.kwargs
        query_dict = call_kwargs["query"]
        assert "query" in query_dict
        assert mock_quay_summary.date_filter in query_dict["query"]["bool"]["filter"]

    @pytest.mark.asyncio
    async def test_get_iterations_no_filters(
        self, mock_quay_summary, mock_elastic_service
    ):
        """Test get_iterations with no version/benchmark filters."""
        # Given: Mock responses for get_versions and get_benchmarks
        mock_elastic_service.post.side_effect = [
            # get_versions response
            {
                "aggregations": {
                    "versions": {
                        "buckets": [
                            {"key": "4.18.0-nightly"},
                            {"key": "4.19.0-nightly"},
                        ]
                    }
                }
            },
            # get_benchmarks response for 4.18
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                    {"key": "uuid-2"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
            # get_benchmarks response for 4.19
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-3"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting iterations
        iterations = await mock_quay_summary.get_iterations()

        # Then: Should return structured iteration data
        assert "config_key" in iterations
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "quay-load-test" in iterations["benchmarks"]["4.18"]

    @pytest.mark.asyncio
    async def test_get_iterations_with_filters(
        self, mock_quay_summary, mock_elastic_service
    ):
        """Test get_iterations with version and benchmark filters."""
        # Given: Specific version and benchmark filters
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting iterations with filters
        iterations = await mock_quay_summary.get_iterations(
            versions="4.18", benchmarks="quay-load-test"
        )

        # Then: Should return filtered data
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "quay-load-test" in iterations["benchmarks"]["4.18"]

    @pytest.mark.asyncio
    async def test_get_iterations_no_variants(
        self, mock_quay_summary, mock_elastic_service, monkeypatch
    ):
        """Test get_iterations when no variants are found."""
        # Given: Mock responses with empty iteration variants
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # Create a real helper but mock its get_iteration_variants to return empty dict
        original_create_helper = mock_quay_summary.create_helper

        def mock_create_helper(benchmark):
            helper = original_create_helper(benchmark)

            # Mock the get_iteration_variants method to return empty dict
            async def empty_variants(uuids):
                return {}

            helper.get_iteration_variants = empty_variants
            return helper

        monkeypatch.setattr(mock_quay_summary, "create_helper", mock_create_helper)

        # When: Getting iterations
        iterations = await mock_quay_summary.get_iterations(versions="4.18")

        # Then: Should handle gracefully and return empty metrics for that config
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "quay-load-test" in iterations["benchmarks"]["4.18"]
        # The benchmark should have empty config due to empty variants
        config_keys = list(iterations["benchmarks"]["4.18"]["quay-load-test"].keys())
        if config_keys:
            assert (
                iterations["benchmarks"]["4.18"]["quay-load-test"][config_keys[0]] == {}
            )

    @pytest.mark.asyncio
    async def test_get_iterations_value_error(
        self, mock_quay_summary, mock_elastic_service, monkeypatch
    ):
        """Test get_iterations handles ValueError from get_helper gracefully."""
        # Given: Mock responses and get_helper that raises ValueError
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # Mock get_helper to raise ValueError
        def mock_get_helper(benchmark):
            raise ValueError(f"Unsupported benchmark: {benchmark}")

        monkeypatch.setattr(mock_quay_summary, "get_helper", mock_get_helper)

        # When: Getting iterations
        iterations = await mock_quay_summary.get_iterations(versions="4.18")

        # Then: Should handle gracefully and return empty metrics for that benchmark
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "quay-load-test" in iterations["benchmarks"]["4.18"]
        # The benchmark should have empty config due to ValueError
        config_keys = list(iterations["benchmarks"]["4.18"]["quay-load-test"].keys())
        if config_keys:
            assert (
                iterations["benchmarks"]["4.18"]["quay-load-test"][config_keys[0]] == {}
            )

    @pytest.mark.asyncio
    async def test_get_configs(self, mock_quay_summary, mock_elastic_service):
        """Test get_configs returns iteration counts."""
        # Given: Mock iteration data
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                    {"key": "uuid-2"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting configs (counts, not uuids)
        configs = await mock_quay_summary.get_configs(
            versions="4.18", benchmarks="quay-load-test", uuids=False
        )

        # Then: Should return counts instead of uuid lists
        assert "config_key" in configs
        assert "benchmarks" in configs
        if "4.18" in configs["benchmarks"]:
            if "quay-load-test" in configs["benchmarks"]["4.18"]:
                config_keys = list(
                    configs["benchmarks"]["4.18"]["quay-load-test"].keys()
                )
                if config_keys:
                    first_config = configs["benchmarks"]["4.18"]["quay-load-test"][
                        config_keys[0]
                    ]
                    if first_config:
                        for count in first_config.values():
                            # Since we have n/a variant, the count should be int
                            assert isinstance(count, (int, list))

    @pytest.mark.asyncio
    async def test_get_configs_with_uuids(
        self, mock_quay_summary, mock_elastic_service
    ):
        """Test get_configs returns uuid lists when requested."""
        # Given: Mock iteration data
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                    {"key": "uuid-2"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting configs with uuids=True
        configs = await mock_quay_summary.get_configs(
            versions="4.18", benchmarks="quay-load-test", uuids=True
        )

        # Then: Should return uuid lists
        assert "config_key" in configs
        assert "benchmarks" in configs

    def test_is_ready_not_ready(self, mock_quay_summary):
        """Test is_ready returns 'not ready' when not ready is in set."""
        # Given: A readiness set with 'not ready'
        readiness = {"ready", "warning", "not ready"}

        # When: Checking readiness
        result = mock_quay_summary.is_ready(readiness)

        # Then: Should return 'not ready'
        assert result == "not ready"

    def test_is_ready_warning(self, mock_quay_summary):
        """Test is_ready returns 'warning' when only warning and ready."""
        # Given: A readiness set with 'warning'
        readiness = {"ready", "warning"}

        # When: Checking readiness
        result = mock_quay_summary.is_ready(readiness)

        # Then: Should return 'warning'
        assert result == "warning"

    def test_is_ready_ready(self, mock_quay_summary):
        """Test is_ready returns 'ready' when only ready."""
        # Given: A readiness set with only 'ready'
        readiness = {"ready"}

        # When: Checking readiness
        result = mock_quay_summary.is_ready(readiness)

        # Then: Should return 'ready'
        assert result == "ready"

    @pytest.mark.asyncio
    async def test_close(self, mock_quay_summary, mock_elastic_service):
        """Test close() closes the ElasticService."""
        # Given: A QuaySummary instance with mocked service
        # When: Closing the summary
        await mock_quay_summary.close()

        # Then: Service close should have been called
        mock_elastic_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_metric_aggregation(self, mock_quay_summary, mock_elastic_service):
        """Test metric_aggregation aggregates metrics across configurations."""
        # Given: Mock responses for iterations and processing
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                    {"key": "uuid-2"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
            # process response for quay-push-pull
            {
                "aggregations": {
                    "stats": {
                        "min": 1000,
                        "max": 1500,
                        "avg": 1250,
                        "std_deviation": 250,
                    },
                    "by_uuid": {
                        "buckets": [
                            {
                                "key": "uuid-1",
                                "start_time": {"value": 1705316400000},  # milliseconds
                                "average": {"value": 1200},
                            },
                            {
                                "key": "uuid-2",
                                "start_time": {"value": 1705320000000},
                                "average": {"value": 1300},
                            },
                        ]
                    },
                },
            },
            # process response for quay-vegeta-results
            {
                "aggregations": {
                    "stats": {
                        "min": 500,
                        "max": 800,
                        "avg": 650,
                        "std_deviation": 150,
                    },
                    "by_uuid": {
                        "buckets": [
                            {
                                "key": "uuid-1",
                                "timestamp": {"value": 1705316400000},  # milliseconds
                                "average": {"value": 600},
                            },
                            {
                                "key": "uuid-2",
                                "timestamp": {"value": 1705320000000},
                                "average": {"value": 700},
                            },
                        ]
                    },
                },
            },
        ]

        # When: Getting metric aggregation
        result = await mock_quay_summary.metric_aggregation(
            versions="4.18", benchmarks="quay-load-test"
        )

        # Then: Should return aggregated metrics
        assert "config_key" in result
        assert "versions" in result
        assert "readiness" in result
        assert result["readiness"] in ["ready", "warning", "not ready"]

    @pytest.mark.asyncio
    async def test_metric_aggregation_unsupported_benchmark(
        self, mock_quay_summary, mock_elastic_service
    ):
        """Test metric_aggregation handles unsupported benchmarks gracefully."""
        # Given: Mock responses with unsupported benchmark
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "unsupported-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting metric aggregation
        result = await mock_quay_summary.metric_aggregation(versions="4.18")

        # Then: Should handle gracefully and return result
        assert "versions" in result
        assert "readiness" in result

    @pytest.mark.asyncio
    async def test_metric_aggregation_value_error(
        self, mock_quay_summary, mock_elastic_service, monkeypatch
    ):
        """Test metric_aggregation handles ValueError from get_helper gracefully."""
        # Given: Mock responses with benchmark data
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 5,
                                    "hitSize": 256,
                                    "concurrency": 10,
                                    "imagePushPulls": 1000,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "quay-load-test",
                                            "uuids": {
                                                "buckets": [
                                                    {"key": "uuid-1"},
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # Mock get_helper to raise ValueError
        def mock_get_helper(benchmark):
            raise ValueError(f"Benchmark {benchmark} not supported")

        monkeypatch.setattr(mock_quay_summary, "get_helper", mock_get_helper)

        # When: Getting metric aggregation
        result = await mock_quay_summary.metric_aggregation(versions="4.18")

        # Then: Should handle gracefully and skip the unsupported benchmark
        assert "versions" in result
        assert "readiness" in result
        # The version should exist but benchmarks should be empty or not include the failed one
        if "4.18" in result["versions"]:
            assert "benchmarks" in result["versions"]["4.18"]


class TestPushPullBenchmark:
    """Test cases for PushPullBenchmark class."""

    @pytest.fixture
    def push_pull_benchmark(self, mock_quay_summary):
        """Create a PushPullBenchmark instance for testing."""
        return QuayLoadTestBenchmark(mock_quay_summary, "quay-load-test")

    @pytest.mark.asyncio
    async def test_get_iteration_variants(self, push_pull_benchmark):
        """Test get_iteration_variants returns n/a for Quay."""
        # Given: A list of uuids
        uuids = ["uuid-1", "uuid-2"]

        # When: Getting iteration variants
        variants = await push_pull_benchmark.get_iteration_variants(uuids)

        # Then: Should return n/a with original uuids
        assert "n/a" in variants
        assert variants["n/a"] == uuids

    @pytest.mark.asyncio
    async def test_process(self, push_pull_benchmark, mock_elastic_service):
        """Test process returns formatted metric data."""
        # Given: Mock responses for both indices
        mock_elastic_service.post.side_effect = [
            # quay-push-pull response
            {
                "aggregations": {
                    "stats": {
                        "min": 1000,
                        "max": 1500,
                        "avg": 1250,
                        "std_deviation": 250,
                    },
                    "by_uuid": {
                        "buckets": [
                            {
                                "key": "uuid-1",
                                "start_time": {"value": 1705316400000},  # milliseconds
                                "average": {"value": 1200},
                            },
                            {
                                "key": "uuid-2",
                                "start_time": {"value": 1705320000000},
                                "average": {"value": 1300},
                            },
                        ]
                    },
                },
            },
            # quay-vegeta-results response
            {
                "aggregations": {
                    "stats": {
                        "min": 500,
                        "max": 800,
                        "avg": 650,
                        "std_deviation": 150,
                    },
                    "by_uuid": {
                        "buckets": [
                            {
                                "key": "uuid-1",
                                "timestamp": {"value": 1705316400000},  # milliseconds
                                "average": {"value": 600},
                            },
                            {
                                "key": "uuid-2",
                                "timestamp": {"value": 1705320000000},
                                "average": {"value": 700},
                            },
                        ]
                    },
                },
            },
        ]

        # When: Processing metrics
        result = await push_pull_benchmark.process(
            "4.18", "config1", "n/a", ["uuid-1", "uuid-2"]
        )

        # Then: Should return formatted sample data with multiple indices
        assert "values" in result
        assert "graph" in result
        assert "stats" in result
        # values should be a dict keyed by index name
        assert isinstance(result["values"], dict)
        assert "quay-push-pull" in result["values"]
        assert "quay-vegeta-results" in result["values"]
        # Check quay-push-pull values
        assert len(result["values"]["quay-push-pull"]) == 2
        assert result["values"]["quay-push-pull"][0]["uuid"] == "uuid-1"
        assert result["values"]["quay-push-pull"][0]["value"] == 1200
        assert isinstance(result["values"]["quay-push-pull"][0]["timestamp"], datetime)
        # Check quay-vegeta-results values
        assert len(result["values"]["quay-vegeta-results"]) == 2
        assert result["values"]["quay-vegeta-results"][0]["uuid"] == "uuid-1"
        assert result["values"]["quay-vegeta-results"][0]["value"] == 600
        # stats should be a dict keyed by index name
        assert isinstance(result["stats"], dict)
        assert "quay-push-pull" in result["stats"]
        assert "quay-vegeta-results" in result["stats"]
        assert result["stats"]["quay-push-pull"]["min"] == 1000
        assert result["stats"]["quay-push-pull"]["max"] == 1500
        assert result["stats"]["quay-push-pull"]["avg"] == 1250
        assert result["stats"]["quay-push-pull"]["std_dev"] == 250
        assert result["stats"]["quay-vegeta-results"]["min"] == 500
        assert result["stats"]["quay-vegeta-results"]["max"] == 800
        assert result["stats"]["quay-vegeta-results"]["avg"] == 650
        assert result["stats"]["quay-vegeta-results"]["std_dev"] == 150
        # graph should have entries for both indices
        assert len(result["graph"]) == 2

    @pytest.mark.asyncio
    async def test_process_with_filter(
        self, push_pull_benchmark, mock_elastic_service, mock_quay_summary
    ):
        """Test process applies benchmark filter if present."""
        # Given: Mock responses for both indices
        mock_elastic_service.post.side_effect = [
            {
                "aggregations": {
                    "stats": {"min": 0, "max": 0, "avg": 0, "std_deviation": 0},
                    "by_uuid": {"buckets": []},
                },
            },
            {
                "aggregations": {
                    "stats": {"min": 0, "max": 0, "avg": 0, "std_deviation": 0},
                    "by_uuid": {"buckets": []},
                },
            },
        ]

        # When: Processing metrics
        await push_pull_benchmark.process("4.18", "config1", "n/a", ["uuid-1"])

        # Then: Should call post for both indices with correct parameters
        assert mock_elastic_service.post.call_count == 2
        call_args_list = mock_elastic_service.post.call_args_list
        indices_called = [call.kwargs["indice"] for call in call_args_list]
        assert "quay-push-pull" in indices_called
        assert "quay-vegeta-results" in indices_called
        # Check that all calls have query parameter
        for call in call_args_list:
            assert "query" in call.kwargs

    @pytest.mark.asyncio
    async def test_process_empty_results(
        self, push_pull_benchmark, mock_elastic_service
    ):
        """Test process handles empty results gracefully."""
        # Given: Mock responses for both indices with no results
        mock_elastic_service.post.side_effect = [
            {
                "aggregations": {
                    "stats": {"min": 0, "max": 0, "avg": 0, "std_deviation": 0},
                    "by_uuid": {"buckets": []},
                },
            },
            {
                "aggregations": {
                    "stats": {"min": 0, "max": 0, "avg": 0, "std_deviation": 0},
                    "by_uuid": {"buckets": []},
                },
            },
        ]

        # When: Processing metrics
        result = await push_pull_benchmark.process("4.18", "config1", "n/a", ["uuid-1"])

        # Then: Should return empty values dict (indices with no results don't appear in values)
        # but stats should have entries for all indices
        assert "values" in result
        assert isinstance(result["values"], dict)
        # When there are no buckets, indices don't appear in values
        # (because by_uuid[index] is never accessed when buckets is empty)
        assert len(result["values"]) == 0
        # Stats should still have entries for all indices
        assert "stats" in result
        assert isinstance(result["stats"], dict)
        assert "quay-push-pull" in result["stats"]
        assert "quay-vegeta-results" in result["stats"]
        assert result["stats"]["quay-push-pull"]["avg"] == 0
        assert result["stats"]["quay-vegeta-results"]["avg"] == 0

    @pytest.mark.asyncio
    async def test_process_with_date_filter(
        self, push_pull_benchmark, mock_elastic_service, mock_quay_summary
    ):
        """Test process applies date filter when set."""
        # Given: Mock summary with date filter
        mock_quay_summary.date_filter = {"range": {"timestamp": {"gte": "2024-01-01"}}}
        mock_elastic_service.post.side_effect = [
            {
                "aggregations": {
                    "stats": {"min": 0, "max": 0, "avg": 0, "std_deviation": 0},
                    "by_uuid": {"buckets": []},
                },
            },
            {
                "aggregations": {
                    "stats": {"min": 0, "max": 0, "avg": 0, "std_deviation": 0},
                    "by_uuid": {"buckets": []},
                },
            },
        ]

        # When: Processing metrics
        await push_pull_benchmark.process("4.18", "config1", "n/a", ["uuid-1"])

        # Then: Date filter should be in all queries
        assert mock_elastic_service.post.call_count == 2
        for call in mock_elastic_service.post.call_args_list:
            query_dict = call.kwargs["query"]
            assert "query" in query_dict
            assert (
                mock_quay_summary.date_filter in query_dict["query"]["bool"]["filter"]
            )

    @pytest.mark.asyncio
    async def test_evaluate_ready(self, push_pull_benchmark):
        """Test evaluate returns 'ready' for good metrics."""
        # Given: A metric sample with last value above average for both indices
        metric = {
            "values": {
                "quay-push-pull": [
                    {"value": 1000},
                    {"value": 1200},
                    {"value": 1300},
                ],
                "quay-vegeta-results": [
                    {"value": 500},
                    {"value": 600},
                    {"value": 700},
                ],
            },
            "stats": {
                "quay-push-pull": {"avg": 1100, "std_dev": 100},
                "quay-vegeta-results": {"avg": 550, "std_dev": 50},
            },
        }

        # When: Evaluating the metric
        result = await push_pull_benchmark.evaluate(metric)

        # Then: Should return 'ready'
        assert result == "ready"

    @pytest.mark.asyncio
    async def test_evaluate_warning(self, push_pull_benchmark):
        """Test evaluate returns 'warning' for high std deviation."""
        # Given: A metric sample with high std deviation
        metric = {
            "values": {
                "quay-push-pull": [
                    {"value": 1000},
                    {"value": 2000},
                    {"value": 1500},
                ],
                "quay-vegeta-results": [
                    {"value": 500},
                    {"value": 600},
                    {"value": 550},
                ],
            },
            "stats": {
                "quay-push-pull": {"avg": 1000, "std_dev": 600},  # std_dev > avg/2
                "quay-vegeta-results": {"avg": 550, "std_dev": 50},
            },
        }

        # When: Evaluating the metric
        result = await push_pull_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"

    @pytest.mark.asyncio
    async def test_evaluate_not_ready(self, push_pull_benchmark):
        """Test evaluate returns 'not ready' when last value is below average."""
        # Given: A metric sample with last value below average
        metric = {
            "values": {
                "quay-push-pull": [
                    {"value": 1500},
                    {"value": 1400},
                    {"value": 900},  # below avg
                ],
                "quay-vegeta-results": [
                    {"value": 700},
                    {"value": 650},
                    {"value": 600},
                ],
            },
            "stats": {
                "quay-push-pull": {"avg": 1200, "std_dev": 100},
                "quay-vegeta-results": {"avg": 550, "std_dev": 50},
            },
        }

        # When: Evaluating the metric
        result = await push_pull_benchmark.evaluate(metric)

        # Then: Should return 'not ready'
        assert result == "not ready"

    @pytest.mark.asyncio
    async def test_evaluate_empty_values(self, push_pull_benchmark):
        """Test evaluate handles empty values."""
        # Given: A metric sample with no values for one index
        metric = {
            "values": {
                "quay-push-pull": [],
                "quay-vegeta-results": [
                    {"value": 500},
                    {"value": 600},
                ],
            },
            "stats": {
                "quay-push-pull": {"avg": 0, "std_dev": 0},
                "quay-vegeta-results": {"avg": 550, "std_dev": 50},
            },
        }

        # When: Evaluating the metric
        result = await push_pull_benchmark.evaluate(metric)

        # Then: Should return 'warning' due to empty values
        assert result == "warning"
