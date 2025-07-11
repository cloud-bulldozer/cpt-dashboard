from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pandas as pd
import pytest

from app.main import app as fastapi_app

"""Unit tests for the OCP graph endpoint.

Assisted-by: Cursor.

This file was generated by Cursor using the following prompt:

    write unit tests for ocpGraph.py

Cursor has an unfortunate tendency to generate unit tests with mocks for
internal module functions, which limits the test coverage. Cursor was able
to fix this (and even clearly explain why it should be done) by telling it
to rewrite the tests without mocking internal functions.

The only problem I fixed manually was an unfortunate misunderstanding of
of Python import paths. Cursor consistently mocked external functions using
the import path rather than the local imported path.
"""


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    yield TestClient(fastapi_app)


@pytest.fixture
def mock_elastic_service():
    """Mock ElasticService."""
    mock_es = AsyncMock()
    mock_es.post = AsyncMock()
    mock_es.close = AsyncMock()
    return mock_es


@pytest.fixture
def sample_uuid():
    """Sample UUID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_meta():
    """Sample metadata for testing."""
    return {
        "benchmark": "cluster-density-ms",
        "masterNodesType": "m6a.xlarge",
        "workerNodesType": "m6a.xlarge",
        "masterNodesCount": 3,
        "workerNodesCount": 24,
        "platform": "AWS",
        "ocpVersion": "4.14.0-rc.4",
    }


@pytest.fixture
def mock_job_summary_response():
    """Mock response for job summary queries."""
    return {
        "data": [
            {
                "_source": {
                    "uuid": "550e8400-e29b-41d4-a716-446655440000",
                    "jobConfig": {"jobIterations": 5},
                }
            },
            {
                "_source": {
                    "uuid": "550e8400-e29b-41d4-a716-446655440001",
                    "jobConfig": {"jobIterations": 5},
                }
            },
        ],
        "total": 2,
    }


@pytest.fixture
def mock_match_runs_response():
    """Mock response for getMatchRuns queries."""
    return {
        "data": [
            {"_source": {"uuid": "550e8400-e29b-41d4-a716-446655440000"}},
            {"_source": {"uuid": "550e8400-e29b-41d4-a716-446655440001"}},
        ],
        "total": 2,
    }


@pytest.fixture
def mock_burner_results_response():
    """Mock response for burner results queries."""
    return {
        "data": [
            {
                "_source": {
                    "uuid": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2023-01-01T10:00:00Z",
                    "quantileName": "Ready",
                    "metricName": "podLatencyQuantilesMeasurement",
                    "P99": 1500,
                }
            },
            {
                "_source": {
                    "uuid": "550e8400-e29b-41d4-a716-446655440001",
                    "timestamp": "2023-01-01T11:00:00Z",
                    "quantileName": "Ready",
                    "metricName": "podLatencyQuantilesMeasurement",
                    "P99": 1600,
                }
            },
        ],
        "total": 2,
    }


@pytest.fixture
def mock_cpu_results_response():
    """Mock response for CPU results aggregation queries."""
    return {
        "aggregations": {
            "time": {
                "buckets": [
                    {
                        "key": "550e8400-e29b-41d4-a716-446655440000",
                        "time": {"value_as_string": "2023-01-01T10:00:00Z"},
                    },
                    {
                        "key": "550e8400-e29b-41d4-a716-446655440001",
                        "time": {"value_as_string": "2023-01-01T11:00:00Z"},
                    },
                ]
            },
            "uuid": {
                "buckets": [
                    {
                        "key": "550e8400-e29b-41d4-a716-446655440000",
                        "cpu": {"value": 0.5},
                    },
                    {
                        "key": "550e8400-e29b-41d4-a716-446655440001",
                        "cpu": {"value": 0.6},
                    },
                ]
            },
        }
    }


@pytest.fixture
def mock_netperf_response():
    """Mock response for netperf queries."""
    return {
        "data": [
            {
                "_source": {
                    "uuid": "550e8400-e29b-41d4-a716-446655440000",
                    "profile": "TCP_STREAM",
                    "messageSize": 1024,
                    "throughput": 1000,
                    "hostNetwork": False,
                    "parallelism": 1,
                    "service": False,
                    "acrossAZ": False,
                    "samples": 10,
                    "test": "test1",
                }
            },
            {
                "_source": {
                    "uuid": "550e8400-e29b-41d4-a716-446655440001",
                    "profile": "TCP_STREAM",
                    "messageSize": 2048,
                    "throughput": 2000,
                    "hostNetwork": False,
                    "parallelism": 1,
                    "service": False,
                    "acrossAZ": False,
                    "samples": 10,
                    "test": "test2",
                }
            },
        ],
        "total": 2,
    }


class TestTrendEndpoint:
    """Test the trend endpoint."""

    @pytest.mark.asyncio
    async def test_trend_success(
        self,
        client,
        mock_elastic_service,
        mock_match_runs_response,
        mock_job_summary_response,
        mock_burner_results_response,
    ):
        """Test successful trend endpoint call."""

        def mock_post_side_effect(query, **kwargs):
            # Mock different responses based on query content
            query_str = str(query)
            if 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "jobStatus: success" in query_str:
                return mock_match_runs_response
            elif "podLatencyQuantilesMeasurement" in query_str:
                return mock_burner_results_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            response = client.get(
                "/api/v1/ocp/graph/trend/4.14.0/24/cluster-density-ms"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert (
            data[0]["name"]
            == "4.14.0 results - PodLatency: Ready 99th%tile ( seconds )"
        )
        assert data[0]["type"] == "scatter"
        assert len(data[0]["y"]) == 2
        assert data[0]["y"] == [1.5, 1.6]  # P99 values divided by 1000

    @pytest.mark.asyncio
    async def test_trend_no_uuids(self, client, mock_elastic_service):
        """Test trend endpoint when no UUIDs are found."""
        mock_elastic_service.post.return_value = {"data": [], "total": 0}

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            response = client.get(
                "/api/v1/ocp/graph/trend/4.14.0/24/cluster-density-ms"
            )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_trend_large_worker_count(
        self,
        client,
        mock_elastic_service,
        mock_match_runs_response,
        mock_job_summary_response,
        mock_burner_results_response,
    ):
        """Test trend endpoint with large worker count (>50)."""

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            # Verify correct instance types are used in query for large worker count
            if "jobStatus: success" in query_str:
                assert "m6a.4xlarge" in query_str  # master nodes
                assert "m5.xlarge" in query_str  # worker nodes
                return mock_match_runs_response
            elif 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "podLatencyQuantilesMeasurement" in query_str:
                return mock_burner_results_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            response = client.get(
                "/api/v1/ocp/graph/trend/4.14.0/100/cluster-density-ms"
            )

        assert response.status_code == 200


class TestDiffCpuEndpoint:
    """Test the diff_cpu endpoint."""

    @pytest.mark.asyncio
    async def test_diff_cpu_success(
        self,
        client,
        mock_elastic_service,
        mock_match_runs_response,
        mock_job_summary_response,
        mock_cpu_results_response,
    ):
        """Test successful diff_cpu endpoint call."""

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            if 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "jobStatus: success" in query_str:
                return mock_match_runs_response
            elif "containerCPU" in query_str:
                return mock_cpu_results_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            response = client.get(
                "/api/v1/ocp/graph/trend/4.14.0/4.13.0/24/cluster-density-ms/cpu/openshift-etcd"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Both versions should be represented
        assert any("4.14.0 results" in item["name"] for item in data)
        assert any("4.13.0 results" in item["name"] for item in data)


class TestTrendCpuEndpoint:
    """Test the trend_cpu endpoint."""

    @pytest.mark.asyncio
    async def test_trend_cpu_success(
        self,
        client,
        mock_elastic_service,
        mock_match_runs_response,
        mock_job_summary_response,
        mock_cpu_results_response,
    ):
        """Test successful trend_cpu endpoint call."""

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            if 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "jobStatus: success" in query_str:
                return mock_match_runs_response
            elif "containerCPU" in query_str:
                return mock_cpu_results_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            response = client.get(
                "/api/v1/ocp/graph/trend/4.14.0/51/cluster-density-ms/cpu/openshift-etcd"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "scatter"
        assert "openshift-etcd avg CPU usage" in data[0]["name"]
        assert len(data[0]["y"]) == 2
        assert data[0]["y"] == [0.5, 0.6]

    @pytest.mark.asyncio
    async def test_trend_cpu_instance_types_medium_count(
        self,
        client,
        mock_elastic_service,
        mock_match_runs_response,
        mock_job_summary_response,
        mock_cpu_results_response,
    ):
        """Test trend_cpu with medium worker count (20-24)."""

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            if "jobStatus: success" in query_str:
                # Verify correct instance types for medium count
                assert "m6a.xlarge" in query_str  # both master and worker nodes
                return mock_match_runs_response
            elif 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "containerCPU" in query_str:
                return mock_cpu_results_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            response = client.get(
                "/api/v1/ocp/graph/trend/4.14.0/24/cluster-density-ms/cpu/openshift-etcd"
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_trend_cpu_instance_types_small_count(
        self,
        client,
        mock_elastic_service,
        mock_match_runs_response,
        mock_job_summary_response,
        mock_cpu_results_response,
    ):
        """Test trend_cpu with small worker count (<= 20)."""

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            if "jobStatus: success" in query_str:
                # Verify correct instance types for small count
                assert "m5.2large" in query_str  # master nodes
                assert "m5.xlarge" in query_str  # worker nodes
                return mock_match_runs_response
            elif 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "containerCPU" in query_str:
                return mock_cpu_results_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            response = client.get(
                "/api/v1/ocp/graph/trend/4.14.0/16/cluster-density-ms/cpu/openshift-etcd"
            )

        assert response.status_code == 200


class TestGraphEndpoint:
    """Test the main graph endpoint."""

    @pytest.mark.asyncio
    async def test_graph_cluster_density(
        self,
        client,
        mock_elastic_service,
        sample_meta,
        mock_match_runs_response,
        mock_job_summary_response,
        mock_burner_results_response,
    ):
        """Test graph endpoint with cluster-density benchmark."""
        sample_meta["benchmark"] = "cluster-density-ms"

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            if 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "jobStatus: success" in query_str:
                return mock_match_runs_response
            elif "podLatencyQuantilesMeasurement" in query_str:
                return mock_burner_results_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ), patch(
            "app.api.v1.endpoints.ocp.graph.getMetadata", return_value=sample_meta
        ):
            response = client.get(
                "/api/v1/ocp/graph/550e8400-e29b-41d4-a716-446655440000"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Previous results p99"
        assert data[1]["name"] == "Current results P99"
        assert data[0]["type"] == "bar"
        assert data[1]["type"] == "bar"

    @pytest.mark.asyncio
    async def test_graph_k8s_netperf(
        self,
        client,
        mock_elastic_service,
        sample_meta,
        mock_match_runs_response,
        mock_netperf_response,
    ):
        """Test graph endpoint with k8s-netperf benchmark."""
        sample_meta["benchmark"] = "k8s-netperf"

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            if "jobStatus: success" in query_str:
                return mock_match_runs_response
            else:
                return mock_netperf_response

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ), patch(
            "app.api.v1.endpoints.ocp.graph.getMetadata", return_value=sample_meta
        ):
            response = client.get(
                "/api/v1/ocp/graph/550e8400-e29b-41d4-a716-446655440000"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Previous results average"
        assert data[1]["name"] == "Current results average"

    @pytest.mark.asyncio
    async def test_graph_ingress_perf(
        self, client, mock_elastic_service, sample_meta, mock_match_runs_response
    ):
        """Test graph endpoint with ingress-perf benchmark (unimplemented)."""
        sample_meta["benchmark"] = "ingress-perf"

        def mock_post_side_effect(query, **kwargs):
            return (
                mock_match_runs_response
                if "jobStatus: success" in str(query)
                else {"data": [], "total": 0}
            )

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ), patch(
            "app.api.v1.endpoints.ocp.graph.getMetadata", return_value=sample_meta
        ):
            response = client.get(
                "/api/v1/ocp/graph/550e8400-e29b-41d4-a716-446655440000"
            )

        assert response.status_code == 200
        data = response.json()
        assert data == []  # ingress-perf returns empty metrics

    @pytest.mark.asyncio
    async def test_graph_virt_density(
        self,
        client,
        mock_elastic_service,
        sample_meta,
        mock_match_runs_response,
        mock_job_summary_response,
    ):
        """Test graph endpoint with virt-density benchmark."""
        sample_meta["benchmark"] = "virt-density"

        # Mock virt-density specific response
        mock_virt_response = {
            "data": [
                {
                    "_source": {
                        "uuid": "550e8400-e29b-41d4-a716-446655440000",
                        "quantileName": "VMReady",
                        "metricName": "vmiLatencyQuantilesMeasurement",
                        "P99": 2500,
                    }
                },
                {
                    "_source": {
                        "uuid": "550e8400-e29b-41d4-a716-446655440001",
                        "quantileName": "VMReady",
                        "metricName": "vmiLatencyQuantilesMeasurement",
                        "P99": 2600,
                    }
                },
            ],
            "total": 2,
        }

        def mock_post_side_effect(query, **kwargs):
            query_str = str(query)

            if 'metricName: "jobSummary"' in query_str:
                return mock_job_summary_response
            elif "jobStatus: success" in query_str:
                return mock_match_runs_response
            elif "vmiLatencyQuantilesMeasurement" in query_str:
                return mock_virt_response
            return {"data": [], "total": 0}

        mock_elastic_service.post.side_effect = mock_post_side_effect

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ), patch(
            "app.api.v1.endpoints.ocp.graph.getMetadata", return_value=sample_meta
        ):
            response = client.get(
                "/api/v1/ocp/graph/550e8400-e29b-41d4-a716-446655440000"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Previous results p99"
        assert data[1]["name"] == "Current results P99"


class TestHelperFunctions:
    """Test helper functions."""

    def test_parse_cpu_results(self):
        """Test parseCPUResults function."""
        from app.api.v1.endpoints.ocp.graph import parseCPUResults

        sample_cpu_results = {
            "aggregations": {
                "time": {
                    "buckets": [
                        {
                            "key": "uuid1",
                            "time": {"value_as_string": "2023-01-01T10:00:00Z"},
                        },
                        {
                            "key": "uuid2",
                            "time": {"value_as_string": "2023-01-01T11:00:00Z"},
                        },
                    ]
                },
                "uuid": {
                    "buckets": [
                        {"key": "uuid1", "cpu": {"value": 0.5}},
                        {"key": "uuid2", "cpu": {"value": 0.6}},
                    ]
                },
            }
        }

        result = parseCPUResults(sample_cpu_results)

        assert len(result) == 2
        assert result[0]["uuid"] == "uuid1"
        assert result[0]["timestamp"] == "2023-01-01T10:00:00Z"
        assert result[0]["cpu_avg"] == 0.5
        assert result[1]["uuid"] == "uuid2"
        assert result[1]["timestamp"] == "2023-01-01T11:00:00Z"
        assert result[1]["cpu_avg"] == 0.6

    @pytest.mark.asyncio
    async def test_job_summary(self, mock_elastic_service):
        """Test jobSummary function."""
        from app.api.v1.endpoints.ocp.graph import jobSummary

        mock_response = {
            "data": [
                {"_source": {"uuid": "uuid1", "jobConfig": {"jobIterations": 5}}},
                {"_source": {"uuid": "uuid2", "jobConfig": {"jobIterations": 5}}},
            ],
            "total": 2,
        }
        mock_elastic_service.post.return_value = mock_response

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            result = await jobSummary(["uuid1", "uuid2"])

        assert len(result) == 2
        assert result[0]["uuid"] == "uuid1"
        assert result[1]["uuid"] == "uuid2"
        mock_elastic_service.close.assert_called_once()

    def test_job_filter_matching_iterations(self):
        """Test jobFilter with matching iterations."""
        from app.api.v1.endpoints.ocp.graph import jobFilter

        sample_data = [
            {"uuid": "uuid1", "jobConfig": {"jobIterations": 5}},
            {"uuid": "uuid2", "jobConfig": {"jobIterations": 5}},
        ]

        result = jobFilter(sample_data, sample_data)

        assert len(result) == 2
        assert "uuid1" in result
        assert "uuid2" in result

    def test_job_filter_empty_data(self):
        """Test jobFilter with empty data."""
        from app.api.v1.endpoints.ocp.graph import jobFilter

        result = jobFilter([], [])
        assert result == []

        result = jobFilter(None, None)
        assert result == []

    def test_burner_filter(self):
        """Test burnerFilter function."""
        from app.api.v1.endpoints.ocp.graph import burnerFilter

        sample_data = [
            {
                "timestamp": "2023-01-01T10:00:00Z",
                "quantileName": "Ready",
                "metricName": "podLatencyQuantilesMeasurement",
                "P99": 1500,
            },
            {
                "timestamp": "2023-01-01T11:00:00Z",
                "quantileName": "Ready",
                "metricName": "podLatencyQuantilesMeasurement",
                "P99": 1600,
            },
        ]

        df = pd.DataFrame(sample_data)
        result = burnerFilter(df)

        assert "quantileName" in result.columns
        assert "metricName" in result.columns
        assert "P99" in result.columns
        assert len(result) == 2

    def test_netperf_filter(self):
        """Test netperfFilter function."""
        from app.api.v1.endpoints.ocp.graph import netperfFilter

        sample_data = [
            {
                "profile": "TCP_STREAM",
                "hostNetwork": False,
                "parallelism": 1,
                "service": False,
                "acrossAZ": False,
                "samples": 10,
                "messageSize": 1024,
                "throughput": 1000,
                "test": "test1",
            },
            {
                "profile": "UDP_STREAM",
                "hostNetwork": True,  # This should be filtered out
                "parallelism": 1,
                "service": False,
                "acrossAZ": False,
                "samples": 10,
                "messageSize": 2048,
                "throughput": 2000,
                "test": "test2",
            },
        ]

        df = pd.DataFrame(sample_data)
        result = netperfFilter(df)

        # Should filter out items with hostNetwork=True
        assert len(result) <= len(sample_data)
        for _, row in result.iterrows():
            assert row["hostNetwork"] is False
            assert row["parallelism"] == 1
            assert "TCP_STREAM" in row["profile"]

    @pytest.mark.asyncio
    async def test_get_burner_results(self, mock_elastic_service):
        """Test getBurnerResults function."""
        from app.api.v1.endpoints.ocp.graph import getBurnerResults

        mock_response = {
            "data": [
                {"_source": {"uuid": "uuid1", "P99": 1500}},
                {"_source": {"uuid": "uuid2", "P99": 1600}},
            ],
            "total": 2,
        }
        mock_elastic_service.post.return_value = mock_response

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            result = await getBurnerResults(
                "", ["uuid1", "uuid2"], "ripsaw-kube-burner*"
            )

        assert len(result) == 2
        assert result[0]["uuid"] == "uuid1"
        assert result[1]["uuid"] == "uuid2"
        mock_elastic_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_burner_results_empty(self):
        """Test getBurnerResults with empty UUIDs."""
        from app.api.v1.endpoints.ocp.graph import getBurnerResults

        result = await getBurnerResults("", [], "ripsaw-kube-burner*")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_match_runs(self, mock_elastic_service, sample_meta):
        """Test getMatchRuns function."""
        from app.api.v1.endpoints.ocp.graph import getMatchRuns

        mock_response = {
            "data": [{"_source": {"uuid": "uuid1"}}, {"_source": {"uuid": "uuid2"}}],
            "total": 2,
        }
        mock_elastic_service.post.return_value = mock_response

        with patch(
            "app.api.v1.endpoints.ocp.graph.ElasticService",
            return_value=mock_elastic_service,
        ):
            result = await getMatchRuns(sample_meta, True)

        assert len(result) == 2
        assert "uuid1" in result
        assert "uuid2" in result
        mock_elastic_service.close.assert_called_once()
