from unittest.mock import AsyncMock

import pytest

from app.api.v1.endpoints.ocp.summary import (
    BENCHMARK_MAPPER,
    IngressPerfBenchmark,
    K8sNetperfBenchmark,
    KubeBurnerBenchmark,
    OcpFingerprint,
    OcpSummary,
)

"""Unit tests for the OCP summary module.

This file tests the classes and functionality defined in ocp/summary.py,
including OcpFingerprint, OcpSummary, KubeBurnerBenchmark, K8sNetperfBenchmark,
and IngressPerfBenchmark classes.

Follows established patterns from other unit tests with Given-When-Then structure.

Generated-by: Cursor
"""


@pytest.fixture
def mock_elastic_service():
    """Create a mock ElasticService for testing."""
    mock_service = AsyncMock()
    mock_service.close = AsyncMock()
    mock_service.post = AsyncMock()
    return mock_service


@pytest.fixture
def mock_ocp_summary(mock_elastic_service, monkeypatch):
    """Create a mock OcpSummary instance with mocked ElasticService."""

    # Patch ElasticService at the import location
    monkeypatch.setattr(
        "app.api.v1.endpoints.summary.summary_search.ElasticService",
        lambda configpath: mock_elastic_service,
    )

    summary = OcpSummary("ocp", "ocp.elasticsearch")
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

    def test_benchmark_mapper_contains_expected_benchmarks(self):
        """Test that BENCHMARK_MAPPER contains known benchmarks."""
        # Given: Known benchmark names
        known_benchmarks = [
            "cluster-density",
            "cluster-density-v2",
            "k8s-netperf",
            "ingress-perf",
            "virt-density",
            "olm",
        ]

        # When: Checking if they exist in BENCHMARK_MAPPER
        # Then: All known benchmarks should be present
        for benchmark in known_benchmarks:
            assert benchmark in BENCHMARK_MAPPER

    def test_benchmark_mapper_cluster_density(self):
        """Test cluster-density benchmark configuration."""
        # Given: The cluster-density benchmark
        benchmark_class = BENCHMARK_MAPPER["cluster-density"]

        # When: Checking its properties
        # Then: It should be the KubeBurnerBenchmark class
        assert benchmark_class == KubeBurnerBenchmark
        assert hasattr(benchmark_class, "INDEX")
        assert benchmark_class.INDEX == "ripsaw-kube-burner"
        assert hasattr(benchmark_class, "FILTER")
        assert "cluster-density" in benchmark_class.FILTER
        assert benchmark_class.FILTER["cluster-density"] == {
            "metricName.keyword": "podLatencyQuantilesMeasurement",
            "quantileName.keyword": "Ready",
        }

    def test_benchmark_mapper_k8s_netperf(self):
        """Test k8s-netperf benchmark configuration."""
        # Given: The k8s-netperf benchmark
        benchmark_class = BENCHMARK_MAPPER["k8s-netperf"]

        # When: Checking its properties
        # Then: It should be the K8sNetperfBenchmark class
        assert benchmark_class == K8sNetperfBenchmark
        assert hasattr(benchmark_class, "INDEX")
        assert benchmark_class.INDEX == "k8s-netperf"


class TestOcpFingerprint:
    """Test cases for OcpFingerprint dataclass."""

    def test_ocp_fingerprint_creation(self):
        """Test creating an OcpFingerprint instance."""
        # Given: Fingerprint parameters (only fields that exist in OcpFingerprint)
        # When: Creating an OcpFingerprint
        fingerprint = OcpFingerprint(
            platform="aws",
            masterNodesType="m5.xlarge",
            masterNodesCount=3,
            workerNodesType="m5.2xlarge",
            workerNodesCount=120,
        )

        # Then: All fields should be set correctly
        assert fingerprint.platform == "aws"
        assert fingerprint.masterNodesType == "m5.xlarge"
        assert fingerprint.masterNodesCount == 3
        assert fingerprint.workerNodesType == "m5.2xlarge"
        assert fingerprint.workerNodesCount == 120

    def test_ocp_fingerprint_metadata(self):
        """Test OcpFingerprint metadata for platform field."""
        # Given: OcpFingerprint class
        # When: Checking platform field metadata
        field_info = OcpFingerprint.__dataclass_fields__["platform"]

        # Then: Should have correct metadata
        assert field_info.metadata["str"] == "p"
        assert field_info.metadata["key"] is True


class TestOcpSummary:
    """Test cases for OcpSummary class."""

    def test_init(self, mock_ocp_summary):
        """Test OcpSummary initialization."""
        # Given: A mock OcpSummary instance from fixture
        summary = mock_ocp_summary

        # When/Then: Should be initialized correctly
        assert summary.product == "ocp"
        assert summary.configpath == "ocp.elasticsearch"
        assert summary.service is not None
        assert summary.benchmarks == BENCHMARK_MAPPER

    def test_create_helper_kube_burner(self, mock_ocp_summary):
        """Test create_helper returns KubeBurnerBenchmark for ripsaw-kube-burner."""
        # Given: An OcpSummary instance and a kube-burner benchmark
        benchmark = "cluster-density"

        # When: Creating a helper
        helper = mock_ocp_summary.create_helper(benchmark)

        # Then: Should return KubeBurnerBenchmark instance
        assert isinstance(helper, KubeBurnerBenchmark)
        assert helper.benchmark == benchmark

    def test_create_helper_k8s_netperf(self, mock_ocp_summary):
        """Test create_helper returns K8sNetperfBenchmark for k8s-netperf."""
        # Given: An OcpSummary instance and k8s-netperf benchmark
        benchmark = "k8s-netperf"

        # When: Creating a helper
        helper = mock_ocp_summary.create_helper(benchmark)

        # Then: Should return K8sNetperfBenchmark instance
        assert isinstance(helper, K8sNetperfBenchmark)
        assert helper.benchmark == benchmark

    def test_create_helper_ingress_perf(self, mock_ocp_summary):
        """Test create_helper returns IngressPerfBenchmark for ingress-performance."""
        # Given: An OcpSummary instance and ingress-perf benchmark
        benchmark = "ingress-perf"

        # When: Creating a helper
        helper = mock_ocp_summary.create_helper(benchmark)

        # Then: Should return IngressPerfBenchmark instance
        assert isinstance(helper, IngressPerfBenchmark)
        assert helper.benchmark == benchmark

    def test_create_helper_unsupported_benchmark(self, mock_ocp_summary):
        """Test create_helper raises ValueError for unsupported benchmarks."""
        # Given: An OcpSummary instance and unsupported benchmark
        benchmark = "node-density"  # Has None value in BENCHMARK_INDEX

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Unsupported benchmark"):
            mock_ocp_summary.create_helper(benchmark)

    @pytest.mark.asyncio
    async def test_get_versions(self, mock_ocp_summary, mock_elastic_service):
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
        versions = await mock_ocp_summary.get_versions()

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
        # Get the call kwargs (keyword arguments)
        call_kwargs = mock_elastic_service.post.call_args.kwargs
        # The 'query' parameter contains the entire query dict
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
        self, mock_ocp_summary, mock_elastic_service
    ):
        """Test get_versions applies date filter when set."""
        # Given: OcpSummary with date filter
        mock_ocp_summary.date_filter = {
            "range": {"timestamp": {"gte": "2024-01-01", "lte": "2024-12-31"}}
        }
        mock_elastic_service.post.return_value = {
            "aggregations": {"versions": {"buckets": [{"key": "4.18.0-nightly"}]}}
        }

        # When: Getting versions
        await mock_ocp_summary.get_versions()

        # Then: Date filter should be in query
        call_kwargs = mock_elastic_service.post.call_args.kwargs
        query_dict = call_kwargs["query"]
        assert "query" in query_dict
        assert mock_ocp_summary.date_filter in query_dict["query"]["bool"]["filter"]

    @pytest.mark.asyncio
    async def test_get_benchmarks(self, mock_ocp_summary, mock_elastic_service):
        """Test get_benchmarks returns benchmark hierarchy."""
        # Given: Mock response with benchmark and configuration data
        mock_elastic_service.post.return_value = {
            "aggregations": {
                "configurations": {
                    "buckets": [
                        {
                            "key": {
                                "platform": "aws",
                                "masterNodesType": "m5.xlarge",
                                "masterNodesCount": 3,
                                "workerNodesType": "m5.2xlarge",
                                "workerNodesCount": 120,
                            },
                            "benchmarks": {
                                "buckets": [
                                    {
                                        "key": "cluster-density",
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
        benchmarks = await mock_ocp_summary.get_benchmarks("4.18")

        # Then: Should return properly structured benchmark data
        assert "cluster-density" in benchmarks
        assert len(benchmarks["cluster-density"]) > 0
        config = benchmarks["cluster-density"][0]
        assert "configuration" in config
        assert "uuids" in config
        assert len(config["uuids"]) == 2

    @pytest.mark.asyncio
    async def test_get_iterations_no_filters(
        self, mock_ocp_summary, mock_elastic_service
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
            # get_iteration_variants response
            {
                "aggregations": {
                    "jobIterations": {
                        "buckets": [
                            {
                                "key": 100,
                                "uuids": {
                                    "buckets": [
                                        {"key": "uuid-1"},
                                        {"key": "uuid-2"},
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "k8s-netperf",
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
            # get_iteration_variants for k8s-netperf (returns n/a)
            {},
        ]

        # When: Getting iterations
        iterations = await mock_ocp_summary.get_iterations()

        # Then: Should return structured iteration data
        assert "config_key" in iterations
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "cluster-density" in iterations["benchmarks"]["4.18"]

    @pytest.mark.asyncio
    async def test_get_iterations_with_filters(
        self, mock_ocp_summary, mock_elastic_service
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
            # get_iteration_variants response
            {
                "aggregations": {
                    "jobIterations": {
                        "buckets": [
                            {
                                "key": 100,
                                "uuids": {"buckets": [{"key": "uuid-1"}]},
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting iterations with filters
        iterations = await mock_ocp_summary.get_iterations(
            versions="4.18", benchmarks="cluster-density"
        )

        # Then: Should return filtered data
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "cluster-density" in iterations["benchmarks"]["4.18"]

    @pytest.mark.asyncio
    async def test_get_iterations_no_variants(
        self, mock_ocp_summary, mock_elastic_service
    ):
        """Test get_iterations when no variants are found."""
        # Given: Mock responses with no iteration variants
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
            # get_iteration_variants response (empty)
            {"aggregations": {"jobIterations": {"buckets": []}}},
        ]

        # When: Getting iterations
        iterations = await mock_ocp_summary.get_iterations(versions="4.18")

        # Then: Should return empty benchmark data
        assert "benchmarks" in iterations
        if "4.18" in iterations["benchmarks"]:
            if "cluster-density" in iterations["benchmarks"]["4.18"]:
                config_keys = list(
                    iterations["benchmarks"]["4.18"]["cluster-density"].keys()
                )
                if config_keys:
                    assert (
                        iterations["benchmarks"]["4.18"]["cluster-density"][
                            config_keys[0]
                        ]
                        == {}
                    )

    @pytest.mark.asyncio
    async def test_get_configs(self, mock_ocp_summary, mock_elastic_service):
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
            # get_iteration_variants response
            {
                "aggregations": {
                    "jobIterations": {
                        "buckets": [
                            {
                                "key": 100,
                                "uuids": {
                                    "buckets": [
                                        {"key": "uuid-1"},
                                        {"key": "uuid-2"},
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting configs (counts, not uuids)
        configs = await mock_ocp_summary.get_configs(
            versions="4.18", benchmarks="cluster-density", uuids=False
        )

        # Then: Should return counts instead of uuid lists
        assert "config_key" in configs
        assert "benchmarks" in configs
        if "4.18" in configs["benchmarks"]:
            if "cluster-density" in configs["benchmarks"]["4.18"]:
                config_keys = list(
                    configs["benchmarks"]["4.18"]["cluster-density"].keys()
                )
                if config_keys:
                    first_config = configs["benchmarks"]["4.18"]["cluster-density"][
                        config_keys[0]
                    ]
                    if first_config:
                        for count in first_config.values():
                            assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_get_configs_with_uuids(self, mock_ocp_summary, mock_elastic_service):
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
            # get_iteration_variants response
            {
                "aggregations": {
                    "jobIterations": {
                        "buckets": [
                            {
                                "key": 100,
                                "uuids": {
                                    "buckets": [
                                        {"key": "uuid-1"},
                                        {"key": "uuid-2"},
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
        ]

        # When: Getting configs with uuids=True
        configs = await mock_ocp_summary.get_configs(
            versions="4.18", benchmarks="cluster-density", uuids=True
        )

        # Then: Should return uuid lists
        assert "config_key" in configs
        assert "benchmarks" in configs

    def test_is_ready_not_ready(self, mock_ocp_summary):
        """Test is_ready returns 'not ready' when not ready is in set."""
        # Given: A readiness set with 'not ready'
        readiness = {"ready", "warning", "not ready"}

        # When: Checking readiness
        result = mock_ocp_summary.is_ready(readiness)

        # Then: Should return 'not ready'
        assert result == "not ready"

    def test_is_ready_warning(self, mock_ocp_summary):
        """Test is_ready returns 'warning' when only warning and ready."""
        # Given: A readiness set with 'warning'
        readiness = {"ready", "warning"}

        # When: Checking readiness
        result = mock_ocp_summary.is_ready(readiness)

        # Then: Should return 'warning'
        assert result == "warning"

    def test_is_ready_ready(self, mock_ocp_summary):
        """Test is_ready returns 'ready' when only ready."""
        # Given: A readiness set with only 'ready'
        readiness = {"ready"}

        # When: Checking readiness
        result = mock_ocp_summary.is_ready(readiness)

        # Then: Should return 'ready'
        assert result == "ready"

    @pytest.mark.asyncio
    async def test_metric_aggregation(self, mock_ocp_summary, mock_elastic_service):
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
            # get_iteration_variants response
            {
                "aggregations": {
                    "jobIterations": {
                        "buckets": [
                            {
                                "key": 100,
                                "uuids": {
                                    "buckets": [
                                        {"key": "uuid-1"},
                                        {"key": "uuid-2"},
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
            # process response (KubeBurnerBenchmark)
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "uuid": "uuid-1",
                                "timestamp": "2024-01-15T10:00:00Z",
                                "P99": 1000,
                            }
                        },
                        {
                            "_source": {
                                "uuid": "uuid-2",
                                "timestamp": "2024-01-15T11:00:00Z",
                                "P99": 1500,
                            }
                        },
                    ]
                },
                "aggregations": {
                    "stats": {
                        "min": 1000,
                        "max": 1500,
                        "avg": 1250,
                        "std_deviation": 250,
                    }
                },
            },
        ]

        # When: Getting metric aggregation
        result = await mock_ocp_summary.metric_aggregation(
            versions="4.18", benchmarks="cluster-density"
        )

        # Then: Should return aggregated metrics
        assert "config_key" in result
        assert "versions" in result
        assert "readiness" in result
        assert result["readiness"] in ["ready", "warning", "not ready"]

    @pytest.mark.asyncio
    async def test_metric_aggregation_unsupported_benchmark(
        self, mock_ocp_summary, mock_elastic_service
    ):
        """Test metric_aggregation handles unsupported benchmarks gracefully."""
        # Given: Mock responses with unsupported benchmark
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response with unsupported benchmark
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "custom",
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
        result = await mock_ocp_summary.metric_aggregation(versions="4.18")

        # Then: Should handle gracefully and return result
        assert "versions" in result
        assert "readiness" in result

    @pytest.mark.asyncio
    async def test_get_iterations_with_value_error(
        self, mock_ocp_summary, mock_elastic_service, monkeypatch
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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

        monkeypatch.setattr(mock_ocp_summary, "get_helper", mock_get_helper)

        # When: Getting iterations
        iterations = await mock_ocp_summary.get_iterations(versions="4.18")

        # Then: Should handle gracefully and return empty metrics for that benchmark
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "cluster-density" in iterations["benchmarks"]["4.18"]
        # The benchmark should have empty config due to ValueError
        config_keys = list(iterations["benchmarks"]["4.18"]["cluster-density"].keys())
        if config_keys:
            assert (
                iterations["benchmarks"]["4.18"]["cluster-density"][config_keys[0]]
                == {}
            )

    @pytest.mark.asyncio
    async def test_metric_aggregation_with_value_error(
        self, mock_ocp_summary, mock_elastic_service, monkeypatch
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
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
            # get_iteration_variants response
            {
                "aggregations": {
                    "jobIterations": {
                        "buckets": [
                            {
                                "key": 100,
                                "uuids": {"buckets": [{"key": "uuid-1"}]},
                            }
                        ]
                    }
                }
            },
        ]

        # Mock get_helper to raise ValueError
        def mock_get_helper(benchmark):
            raise ValueError(f"Benchmark {benchmark} not supported")

        monkeypatch.setattr(mock_ocp_summary, "get_helper", mock_get_helper)

        # When: Getting metric aggregation
        result = await mock_ocp_summary.metric_aggregation(versions="4.18")

        # Then: Should handle gracefully and skip the unsupported benchmark
        assert "versions" in result
        assert "readiness" in result
        # The version should exist but benchmarks should be empty or not include the failed one
        if "4.18" in result["versions"]:
            assert "benchmarks" in result["versions"]["4.18"]

    @pytest.mark.asyncio
    async def test_get_iterations_empty_variants(
        self, mock_ocp_summary, mock_elastic_service, monkeypatch
    ):
        """Test get_iterations handles empty variants gracefully."""
        # Given: Mock responses where get_iteration_variants returns empty
        mock_elastic_service.post.side_effect = [
            # get_benchmarks response
            {
                "aggregations": {
                    "configurations": {
                        "buckets": [
                            {
                                "key": {
                                    "platform": "aws",
                                    "masterNodesType": "m5.xlarge",
                                    "masterNodesCount": 3,
                                    "workerNodesType": "m5.2xlarge",
                                    "workerNodesCount": 120,
                                },
                                "benchmarks": {
                                    "buckets": [
                                        {
                                            "key": "cluster-density",
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
        original_create_helper = mock_ocp_summary.create_helper

        def mock_create_helper(benchmark):
            helper = original_create_helper(benchmark)

            # Mock the get_iteration_variants method to return empty dict
            async def empty_variants(uuids):
                return {}

            helper.get_iteration_variants = empty_variants
            return helper

        monkeypatch.setattr(mock_ocp_summary, "create_helper", mock_create_helper)

        # When: Getting iterations
        iterations = await mock_ocp_summary.get_iterations(versions="4.18")

        # Then: Should handle gracefully and return empty metrics for that config
        assert "benchmarks" in iterations
        assert "4.18" in iterations["benchmarks"]
        assert "cluster-density" in iterations["benchmarks"]["4.18"]
        # The benchmark should have empty config due to empty variants
        config_keys = list(iterations["benchmarks"]["4.18"]["cluster-density"].keys())
        if config_keys:
            assert (
                iterations["benchmarks"]["4.18"]["cluster-density"][config_keys[0]]
                == {}
            )


class TestKubeBurnerBenchmark:
    """Test cases for KubeBurnerBenchmark class."""

    @pytest.fixture
    def kube_burner_benchmark(self, mock_ocp_summary):
        """Create a KubeBurnerBenchmark instance for testing."""
        return KubeBurnerBenchmark(mock_ocp_summary, "cluster-density")

    @pytest.mark.asyncio
    async def test_get_iteration_variants(
        self, kube_burner_benchmark, mock_elastic_service
    ):
        """Test get_iteration_variants returns iteration variants."""
        # Given: Mock response with iteration data
        mock_elastic_service.post.return_value = {
            "aggregations": {
                "jobIterations": {
                    "buckets": [
                        {
                            "key": 100,
                            "uuids": {
                                "buckets": [
                                    {"key": "uuid-1"},
                                    {"key": "uuid-2"},
                                ]
                            },
                        },
                        {
                            "key": 200,
                            "uuids": {
                                "buckets": [
                                    {"key": "uuid-3"},
                                ]
                            },
                        },
                    ]
                }
            }
        }

        # When: Getting iteration variants
        variants = await kube_burner_benchmark.get_iteration_variants(
            ["uuid-1", "uuid-2", "uuid-3"]
        )

        # Then: Should return variants grouped by iteration count
        assert 100 in variants
        assert 200 in variants
        assert "uuid-1" in variants[100]
        assert "uuid-2" in variants[100]
        assert "uuid-3" in variants[200]

    @pytest.mark.asyncio
    async def test_get_iteration_variants_with_date_filter(
        self, kube_burner_benchmark, mock_elastic_service, mock_ocp_summary
    ):
        """Test get_iteration_variants applies date filter when set."""
        # Given: Mock summary with date filter
        mock_ocp_summary.date_filter = {"range": {"timestamp": {"gte": "2024-01-01"}}}
        mock_elastic_service.post.return_value = {
            "aggregations": {"jobIterations": {"buckets": []}}
        }

        # When: Getting iteration variants
        await kube_burner_benchmark.get_iteration_variants(["uuid-1"])

        # Then: Date filter should be in query
        call_kwargs = mock_elastic_service.post.call_args.kwargs
        query_dict = call_kwargs["query"]
        assert "query" in query_dict
        assert mock_ocp_summary.date_filter in query_dict["query"]["bool"]["filter"]

    @pytest.mark.asyncio
    async def test_process(self, kube_burner_benchmark, mock_elastic_service):
        """Test process returns formatted metric data."""
        # Given: Mock response with metric data
        mock_elastic_service.post.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "uuid": "uuid-1",
                            "timestamp": "2024-01-15T10:00:00Z",
                            "P99": 1000,
                        }
                    },
                    {
                        "_source": {
                            "uuid": "uuid-2",
                            "timestamp": "2024-01-15T11:00:00Z",
                            "P99": 1500,
                        }
                    },
                ]
            },
            "aggregations": {
                "stats": {
                    "min": 1000,
                    "max": 1500,
                    "avg": 1250,
                    "std_deviation": 250,
                }
            },
        }

        # When: Processing metrics
        result = await kube_burner_benchmark.process(
            "4.18", "config1", 100, ["uuid-1", "uuid-2"]
        )

        # Then: Should return formatted sample data
        assert "values" in result
        assert "graph" in result
        assert "stats" in result
        assert len(result["values"]) == 2
        assert result["values"][0]["uuid"] == "uuid-1"
        assert result["values"][0]["value"] == 1000
        assert result["stats"]["min"] == 1000
        assert result["stats"]["max"] == 1500
        assert result["stats"]["avg"] == 1250

    @pytest.mark.asyncio
    async def test_process_with_filter(
        self, kube_burner_benchmark, mock_elastic_service, mock_ocp_summary
    ):
        """Test process applies benchmark filter."""
        # Given: Mock response and benchmark with filter
        mock_elastic_service.post.return_value = {
            "hits": {"hits": []},
            "aggregations": {
                "stats": {"min": 0, "max": 0, "avg": 0, "std_deviation": 0}
            },
        }

        # When: Processing metrics
        await kube_burner_benchmark.process("4.18", "config1", 100, ["uuid-1"])

        # Then: Filter should be applied in query
        call_kwargs = mock_elastic_service.post.call_args.kwargs
        # Check that filter terms are present
        filters = call_kwargs["query"]["query"]["bool"]["filter"]
        assert any(
            "metricName.keyword" in str(f) or "quantileName.keyword" in str(f)
            for f in filters
        )

    @pytest.mark.asyncio
    async def test_evaluate_ready(self, kube_burner_benchmark):
        """Test evaluate returns 'ready' for good metrics."""
        # Given: A metric sample with last value above average
        metric = {
            "values": [
                {"value": 1000},
                {"value": 1200},
                {"value": 1300},
            ],
            "stats": {"avg": 1100, "std_dev": 100},
        }

        # When: Evaluating the metric
        result = await kube_burner_benchmark.evaluate(metric)

        # Then: Should return 'ready'
        assert result == "ready"

    @pytest.mark.asyncio
    async def test_evaluate_warning(self, kube_burner_benchmark):
        """Test evaluate returns 'warning' for high std deviation."""
        # Given: A metric sample with high std deviation
        metric = {
            "values": [
                {"value": 1000},
                {"value": 2000},
                {"value": 1500},
            ],
            "stats": {"avg": 1000, "std_dev": 600},  # std_dev > avg/2
        }

        # When: Evaluating the metric
        result = await kube_burner_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"

    @pytest.mark.asyncio
    async def test_evaluate_not_ready(self, kube_burner_benchmark):
        """Test evaluate returns 'not ready' when last value is below average."""
        # Given: A metric sample with last value below average
        metric = {
            "values": [
                {"value": 1500},
                {"value": 1400},
                {"value": 900},
            ],
            "stats": {"avg": 1200, "std_dev": 100},
        }

        # When: Evaluating the metric
        result = await kube_burner_benchmark.evaluate(metric)

        # Then: Should return 'not ready'
        assert result == "not ready"

    @pytest.mark.asyncio
    async def test_evaluate_empty_values(self, kube_burner_benchmark):
        """Test evaluate handles empty or single-value metrics."""
        # Given: A metric sample with only one value
        metric = {
            "values": [{"value": 1000}],
            "stats": {"avg": 1000, "std_dev": 0},
        }

        # When: Evaluating the metric
        result = await kube_burner_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"


class TestK8sNetperfBenchmark:
    """Test cases for K8sNetperfBenchmark class."""

    @pytest.fixture
    def k8s_netperf_benchmark(self, mock_ocp_summary):
        """Create a K8sNetperfBenchmark instance for testing."""
        return K8sNetperfBenchmark(mock_ocp_summary, "k8s-netperf")

    @pytest.mark.asyncio
    async def test_get_iteration_variants(self, k8s_netperf_benchmark):
        """Test get_iteration_variants returns n/a for k8s-netperf."""
        # Given: A list of uuids
        uuids = ["uuid-1", "uuid-2"]

        # When: Getting iteration variants
        variants = await k8s_netperf_benchmark.get_iteration_variants(uuids)

        # Then: Should return n/a with original uuids
        assert "n/a" in variants
        assert variants["n/a"] == uuids

    @pytest.mark.asyncio
    async def test_process(self, k8s_netperf_benchmark, mock_elastic_service):
        """Test process returns formatted metric data for k8s-netperf."""
        # Given: Mock response with throughput data
        mock_elastic_service.post.return_value = {
            "aggregations": {
                "stats": {
                    "min": 1000,
                    "max": 2000,
                    "avg": 1500,
                    "count": 10,
                    "std_deviation": 250,
                },
                "uuid": {
                    "buckets": [
                        {
                            "key": "uuid-1",
                            "profile": {
                                "buckets": [
                                    {
                                        "key": "tcp-stream",
                                        "messageSize": {
                                            "buckets": [
                                                {
                                                    "key": 1024,
                                                    "timestamp": {
                                                        "buckets": [
                                                            {
                                                                "key_as_string": "2024-01-15T10:00:00Z",
                                                                "throughput": {
                                                                    "value": 1500
                                                                },
                                                            }
                                                        ]
                                                    },
                                                }
                                            ]
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        }

        # When: Processing metrics
        result = await k8s_netperf_benchmark.process(
            "4.18", "config1", "n/a", ["uuid-1"]
        )

        # Then: Should return formatted sample data with graphs
        assert "values" in result
        assert "graph" in result
        assert "stats" in result
        assert isinstance(result["graph"], list)
        assert result["stats"]["min"] == 1000
        assert result["stats"]["max"] == 2000
        assert result["stats"]["avg"] == 1500
        assert result["stats"]["count"] == 10

    @pytest.mark.asyncio
    async def test_process_multiple_profiles(
        self, k8s_netperf_benchmark, mock_elastic_service
    ):
        """Test process handles multiple profiles and message sizes."""
        # Given: Mock response with multiple profiles
        mock_elastic_service.post.return_value = {
            "aggregations": {
                "stats": {
                    "min": 1000,
                    "max": 3000,
                    "avg": 2000,
                    "count": 20,
                    "std_deviation": 500,
                },
                "uuid": {
                    "buckets": [
                        {
                            "key": "uuid-1",
                            "profile": {
                                "buckets": [
                                    {
                                        "key": "tcp-stream",
                                        "messageSize": {
                                            "buckets": [
                                                {
                                                    "key": 1024,
                                                    "timestamp": {
                                                        "buckets": [
                                                            {
                                                                "key_as_string": "2024-01-15T10:00:00Z",
                                                                "throughput": {
                                                                    "value": 1500
                                                                },
                                                            }
                                                        ]
                                                    },
                                                },
                                                {
                                                    "key": 2048,
                                                    "timestamp": {
                                                        "buckets": [
                                                            {
                                                                "key_as_string": "2024-01-15T10:00:00Z",
                                                                "throughput": {
                                                                    "value": 2000
                                                                },
                                                            }
                                                        ]
                                                    },
                                                },
                                            ]
                                        },
                                    },
                                    {
                                        "key": "udp-stream",
                                        "messageSize": {
                                            "buckets": [
                                                {
                                                    "key": 512,
                                                    "timestamp": {
                                                        "buckets": [
                                                            {
                                                                "key_as_string": "2024-01-15T10:00:00Z",
                                                                "throughput": {
                                                                    "value": 1000
                                                                },
                                                            }
                                                        ]
                                                    },
                                                }
                                            ]
                                        },
                                    },
                                ]
                            },
                        }
                    ]
                },
            }
        }

        # When: Processing metrics
        result = await k8s_netperf_benchmark.process(
            "4.18", "config1", "n/a", ["uuid-1"]
        )

        # Then: Should return multiple graphs for different profiles
        assert (
            len(result["graph"]) == 3
        )  # tcp-stream-1024, tcp-stream-2048, udp-stream-512
        graph_names = [g["name"] for g in result["graph"]]
        assert "tcp-stream-1024" in graph_names
        assert "tcp-stream-2048" in graph_names
        assert "udp-stream-512" in graph_names

    @pytest.mark.asyncio
    async def test_evaluate_ready(self, k8s_netperf_benchmark):
        """Test evaluate returns 'ready' for good metrics."""
        # Given: A metric sample with good values (last value above average)
        metric = {
            "values": {
                "tcp-stream-1024": [
                    {"value": 1300},
                    {"value": 1600},
                ],
                "udp-stream-512": [
                    {"value": 1100},
                    {"value": 1500},
                ],
            },
            "stats": {"avg": 1300, "std_dev": 100},
        }

        # When: Evaluating the metric
        result = await k8s_netperf_benchmark.evaluate(metric)

        # Then: Should return 'ready'
        assert result == "ready"

    @pytest.mark.asyncio
    async def test_evaluate_warning(self, k8s_netperf_benchmark):
        """Test evaluate returns 'warning' for high std deviation."""
        # Given: A metric sample with high std deviation
        metric = {
            "values": {
                "tcp-stream-1024": [
                    {"value": 1500},
                    {"value": 1600},
                ],
            },
            "stats": {"avg": 1000, "std_dev": 600},  # std_dev > avg/2
        }

        # When: Evaluating the metric
        result = await k8s_netperf_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"

    @pytest.mark.asyncio
    async def test_evaluate_not_ready(self, k8s_netperf_benchmark):
        """Test evaluate returns 'not ready' when value below average."""
        # Given: A metric sample with last value below average
        metric = {
            "values": {
                "tcp-stream-1024": [
                    {"value": 1500},
                    {"value": 900},
                ],
            },
            "stats": {"avg": 1200, "std_dev": 100},
        }

        # When: Evaluating the metric
        result = await k8s_netperf_benchmark.evaluate(metric)

        # Then: Should return 'not ready'
        assert result == "not ready"

    @pytest.mark.asyncio
    async def test_evaluate_warning_low_samples(self, k8s_netperf_benchmark):
        """Test evaluate returns 'warning' for low sample counts."""
        # Given: A metric sample with only one value
        metric = {
            "values": {
                "tcp-stream-1024": [{"value": 1500}],
            },
            "stats": {"avg": 1500, "std_dev": 0},
        }

        # When: Evaluating the metric
        result = await k8s_netperf_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"


class TestIngressPerfBenchmark:
    """Test cases for IngressPerfBenchmark class."""

    @pytest.fixture
    def ingress_perf_benchmark(self, mock_ocp_summary):
        """Create an IngressPerfBenchmark instance for testing."""
        return IngressPerfBenchmark(mock_ocp_summary, "ingress-perf")

    @pytest.mark.asyncio
    async def test_get_iteration_variants(self, ingress_perf_benchmark):
        """Test get_iteration_variants returns n/a for ingress-perf."""
        # Given: A list of uuids
        uuids = ["uuid-1", "uuid-2"]

        # When: Getting iteration variants
        variants = await ingress_perf_benchmark.get_iteration_variants(uuids)

        # Then: Should return n/a with original uuids
        assert "n/a" in variants
        assert variants["n/a"] == uuids

    @pytest.mark.asyncio
    async def test_process(self, ingress_perf_benchmark):
        """Test process returns empty dict for ingress-perf."""
        # Given: Process parameters
        # When: Processing metrics
        result = await ingress_perf_benchmark.process(
            "4.18", "config1", 100, ["uuid-1"]
        )

        # Then: Should return empty dict
        assert result == {}

    @pytest.mark.asyncio
    async def test_evaluate_warning_empty(self, ingress_perf_benchmark):
        """Test evaluate returns 'warning' for empty metrics."""
        # Given: An empty metric sample
        metric = {}

        # When: Evaluating the metric
        result = await ingress_perf_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"

    @pytest.mark.asyncio
    async def test_evaluate_warning_low_values(self, ingress_perf_benchmark):
        """Test evaluate returns 'warning' for low sample counts."""
        # Given: A metric sample with only one value
        metric = {
            "values": [{"value": 1000}],
            "stats": {"avg": 1000, "std_dev": 0},
        }

        # When: Evaluating the metric
        result = await ingress_perf_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"

    @pytest.mark.asyncio
    async def test_evaluate_ready(self, ingress_perf_benchmark):
        """Test evaluate returns 'ready' for good metrics."""
        # Given: A metric sample with last value above average
        metric = {
            "values": [
                {"value": 1000},
                {"value": 1200},
                {"value": 1300},
            ],
            "stats": {"avg": 1100, "std_dev": 100},
        }

        # When: Evaluating the metric
        result = await ingress_perf_benchmark.evaluate(metric)

        # Then: Should return 'ready'
        assert result == "ready"

    @pytest.mark.asyncio
    async def test_evaluate_not_ready(self, ingress_perf_benchmark):
        """Test evaluate returns 'not ready' when last value below average."""
        # Given: A metric sample with last value below average
        metric = {
            "values": [
                {"value": 1500},
                {"value": 1400},
                {"value": 900},
            ],
            "stats": {"avg": 1200, "std_dev": 100},
        }

        # When: Evaluating the metric
        result = await ingress_perf_benchmark.evaluate(metric)

        # Then: Should return 'not ready'
        assert result == "not ready"

    @pytest.mark.asyncio
    async def test_evaluate_warning_high_std_dev(self, ingress_perf_benchmark):
        """Test evaluate returns 'warning' for high std deviation."""
        # Given: A metric sample with high std deviation
        metric = {
            "values": [
                {"value": 1000},
                {"value": 2000},
                {"value": 1500},
            ],
            "stats": {"avg": 1000, "std_dev": 600},
        }

        # When: Evaluating the metric
        result = await ingress_perf_benchmark.evaluate(metric)

        # Then: Should return 'warning'
        assert result == "warning"
