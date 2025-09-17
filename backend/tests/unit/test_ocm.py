from datetime import date

import pandas as pd
import pytest

from app.api.v1.commons import ocm

"""Unit tests for the OCM (OpenShift Cluster Manager) data retrieval functions.

Tests the main OCM functions for getting data and filter data from Elasticsearch,
including various filtering, edge case scenarios, and DataFrame processing logic.
"""


class TestGetData:
    """Test cases for ocm.getData function"""

    @pytest.mark.asyncio
    async def test_get_ocm_results(self, fake_elastic_service):
        """Test getData returns OCM cluster results properly formatted."""
        # Raw source data from Elasticsearch
        raw_ocm_data = [
            {
                "clusterId": "cluster-001",
                "metrics.earliest": "2024-01-15T10:30:00.000000",
                "metrics.success": 0.85,
                "buildUrl": "https://jenkins.example.com/build/123",
                "ciSystem": "Jenkins",
            },
            {
                "clusterId": "cluster-002",
                "metrics.earliest": "2024-01-16T14:20:00.000000",
                "metrics.success": 0.30,
                "buildUrl": "",
                "ciSystem": "Airflow",
            },
        ]

        # Expected result after processing
        expected_result = {
            "total": 2,
            "job_statuses": ["success", "failure"],
            "build_urls": ["https://jenkins.example.com/build/123", ""],
            "ci_systems": ["Jenkins", "Airflow"],
            "cluster_ids": ["cluster-001", "cluster-002"],
            "metrics_earliest": [
                "2024-01-15T10:30:00.000000",
                "2024-01-16T14:20:00.000000",
            ],
            "metrics_success": [0.85, 0.30],
        }

        # Set up mock response using set_post_response
        fake_elastic_service.set_post_response(
            response_type="post", data_list=raw_ocm_data
        )

        # Call the function
        result = await ocm.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            filter="clusterId=cluster-001",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert isinstance(result["data"], pd.DataFrame)
        assert result["total"] == expected_result["total"]
        assert result["data"]["jobStatus"].tolist() == expected_result["job_statuses"]
        assert result["data"]["buildUrl"].tolist() == expected_result["build_urls"]
        assert result["data"]["ciSystem"].tolist() == expected_result["ci_systems"]
        assert result["data"]["clusterId"].tolist() == expected_result["cluster_ids"]
        assert (
            result["data"]["metrics.earliest"].tolist()
            == expected_result["metrics_earliest"]
        )
        assert (
            result["data"]["metrics.success"].tolist()
            == expected_result["metrics_success"]
        )

    @pytest.mark.asyncio
    async def test_get_ocm_empty_results(self, fake_elastic_service):
        """Test getData handles empty OCM results gracefully."""
        # Expected result for empty data
        expected_result = {"total": 0}

        # Set up mock response for empty results
        fake_elastic_service.set_post_response(response_type="post", data_list=[])

        # Call the function
        result = await ocm.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert isinstance(result["data"], pd.DataFrame)
        assert result["total"] == expected_result["total"]

    @pytest.mark.asyncio
    async def test_get_ocm_missing_columns(self, fake_elastic_service):
        """Test getData properly handles missing buildUrl and ciSystem columns."""
        # Raw data without buildUrl and ciSystem columns
        raw_ocm_data = [
            {
                "clusterId": "cluster-003",
                "metrics.earliest": "2024-01-17T09:15:00.000000",
                "metrics.success": 0.65,
            }
        ]

        # Expected result with default column values
        expected_result = {
            "total": 1,
            "build_url_default": "",
            "ci_system_default": "",
            "job_status": "unstable",  # 0.65 success rate
            "cluster_id": "cluster-003",
            "metrics_earliest": "2024-01-17T09:15:00.000000",
            "metrics_success": 0.65,
        }

        # Set up mock response
        fake_elastic_service.set_post_response(
            response_type="post", data_list=raw_ocm_data
        )

        # Call the function
        result = await ocm.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            filter="",
            configpath="TEST",
        )

        # Verify results - columns should be added with empty strings
        assert isinstance(result, dict)
        assert isinstance(result["data"], pd.DataFrame)
        assert result["total"] == expected_result["total"]
        assert (
            result["data"]["buildUrl"].iloc[0] == expected_result["build_url_default"]
        )
        assert (
            result["data"]["ciSystem"].iloc[0] == expected_result["ci_system_default"]
        )
        assert result["data"]["jobStatus"].iloc[0] == expected_result["job_status"]
        assert result["data"]["clusterId"].iloc[0] == expected_result["cluster_id"]
        assert (
            result["data"]["metrics.earliest"].iloc[0]
            == expected_result["metrics_earliest"]
        )
        assert (
            result["data"]["metrics.success"].iloc[0]
            == expected_result["metrics_success"]
        )


class TestGetFilterData:
    """Test cases for ocm.getFilterData function"""

    @pytest.mark.asyncio
    async def test_get_ocm_filter_aggregations(self, fake_elastic_service):
        """Test getFilterData returns proper OCM filter aggregations."""
        # Raw aggregation data from Elasticsearch
        raw_aggregations = {
            "clusterId": [
                {"key": "cluster-prod-001", "doc_count": 45},
                {"key": "cluster-stage-002", "doc_count": 30},
            ],
            "jobStatus": [
                {"key": "success", "doc_count": 60},
                {"key": "failure", "doc_count": 15},
            ],
        }

        # Expected final result after OCM filter processing
        expected_result = {
            "filterData": raw_aggregations,
            "summary": {"totalClusters": 75},
        }

        # Set up mock response for filterPost
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            total=0,
            filter_data=raw_aggregations,
            summary={"totalClusters": 75},
        )

        # Call the function
        result = await ocm.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="clusterId=cluster-prod",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["filterData"] == expected_result["filterData"]
        assert result["summary"] == expected_result["summary"]

    @pytest.mark.asyncio
    async def test_get_ocm_filter_no_filter(self, fake_elastic_service):
        """Test getFilterData works without filters for OCM data."""
        # Raw aggregation data from Elasticsearch
        raw_aggregations = {
            "metrics.success": [
                {"key": "success", "doc_count": 120},
                {"key": "failure", "doc_count": 25},
                {"key": "unstable", "doc_count": 10},
            ]
        }

        # Expected final result after OCM filter processing
        expected_result = {"filterData": raw_aggregations, "summary": {}}

        # Set up mock response for filterPost
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            total=0,
            filter_data=raw_aggregations,
            summary={},
        )

        # Call the function
        result = await ocm.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["filterData"] == expected_result["filterData"]
        assert result["summary"] == expected_result["summary"]


class TestHelperFunctions:
    """Test cases for OCM helper functions"""

    def test_fill_ci_system_jenkins(self):
        """Test fillCiSystem returns Jenkins for dates after 2024-06-24."""
        # Test data with date after cutoff
        row = {"metrics.earliest": "2024-07-01T10:30:00.000000Z"}
        expected_result = "Jenkins"

        result = ocm.fillCiSystem(row)

        assert result == expected_result

    def test_fill_ci_system_airflow(self):
        """Test fillCiSystem returns Airflow for dates before 2024-06-24."""
        # Test data with date before cutoff
        row = {"metrics.earliest": "2024-06-01T10:30:00.000000Z"}
        expected_result = "Airflow"

        result = ocm.fillCiSystem(row)

        assert result == expected_result

    def test_convert_job_status_success(self):
        """Test convertJobStatus returns success for high success rates."""
        # Test data with high success rate
        row = {"metrics.success": 0.85}
        expected_result = "success"

        result = ocm.convertJobStatus(row)

        assert result == expected_result

    def test_convert_job_status_failure(self):
        """Test convertJobStatus returns failure for low success rates."""
        # Test data with low success rate
        row = {"metrics.success": 0.25}
        expected_result = "failure"

        result = ocm.convertJobStatus(row)

        assert result == expected_result

    def test_convert_job_status_unstable(self):
        """Test convertJobStatus returns unstable for medium success rates."""
        # Test data with medium success rate
        row = {"metrics.success": 0.60}
        expected_result = "unstable"

        result = ocm.convertJobStatus(row)

        assert result == expected_result

    def test_convert_job_status_boundary_values(self):
        """Test convertJobStatus boundary values."""

        # Test exactly at 0.80 boundary
        row_80 = {"metrics.success": 0.80}
        assert ocm.convertJobStatus(row_80) == "success"

        # Test just below 0.80 boundary
        row_79 = {"metrics.success": 0.79}
        assert ocm.convertJobStatus(row_79) == "unstable"

        # Test exactly at 0.40 boundary
        row_40 = {"metrics.success": 0.40}
        assert ocm.convertJobStatus(row_40) == "unstable"

        # Test just below 0.40 boundary
        row_39 = {"metrics.success": 0.39}
        assert ocm.convertJobStatus(row_39) == "failure"


class TestOCMErrorHandling:
    """Test cases for error handling in OCM functions"""

    @pytest.mark.asyncio
    async def test_ocm_index_not_found(self, fake_elastic_service):
        """Test OCM functions handle missing Elasticsearch index."""
        # Set up the service to raise an exception
        fake_elastic_service.set_post_response(
            response_type="post", error=Exception("Index not found")
        )

        # Verify exception is raised
        with pytest.raises(Exception, match="Index not found"):
            await ocm.getData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                size=10,
                offset=0,
                filter="",
                configpath="TEST",
            )

    @pytest.mark.asyncio
    async def test_ocm_filter_index_not_found(self, fake_elastic_service):
        """Test getFilterData handles missing Elasticsearch index."""
        # Set up the service to raise an exception
        fake_elastic_service.set_post_response(
            response_type="filterPost", error=Exception("Index not found")
        )

        # Verify exception is raised
        with pytest.raises(Exception, match="Index not found"):
            await ocm.getFilterData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                filter="",
                configpath="TEST",
            )
