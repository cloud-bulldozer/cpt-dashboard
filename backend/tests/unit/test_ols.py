from datetime import date

import pytest

from app.api.v1.commons import ols

"""Unit tests for the OLS (OpenShift Lightspeed Service) data retrieval functions.

Tests the main OLS functions for getting filter data from Elasticsearch,
including various filtering and edge case scenarios using shared fixtures approach.
"""


class TestGetFilterData:
    """Test cases for ols.getFilterData function"""

    @pytest.mark.asyncio
    async def test_get_ols_filter_aggregations(self, fake_elastic_service):
        """Test getFilterData returns proper OLS filter aggregations."""
        # Raw aggregation data from Elasticsearch
        raw_aggregations = {
            "benchmark": [
                {"key": "ols-performance-test", "doc_count": 45},
                {"key": "ols-accuracy-test", "doc_count": 30},
            ],
            "releaseStream": [
                {"key": "4.15.0-0.nightly", "doc_count": 35},
                {"key": "4.14.5", "doc_count": 40},
            ],
            "platform": [
                {"key": "aws", "doc_count": 50},
                {"key": "gcp", "doc_count": 25},
            ],
            "jobStatus": [
                {"key": "success", "doc_count": 60},
                {"key": "failure", "doc_count": 15},
            ],
            "olsTestDuration": [
                {"key": "short", "doc_count": 40},
                {"key": "medium", "doc_count": 25},
                {"key": "long", "doc_count": 10},
            ],
        }

        # Raw summary data from Elasticsearch
        raw_summary = {"totalTests": 75, "avgWorkers": 8.5, "avgDuration": 145.2}

        # Expected final result after OLS filter processing
        expected_result = {
            "total": 75,
            "filterData": raw_aggregations,
            "summary": raw_summary,
            "aggregation_keys": [
                "benchmark",
                "releaseStream",
                "platform",
                "jobStatus",
                "olsTestDuration",
            ],
            "test_counts": {"ols-performance-test": 45, "ols-accuracy-test": 30},
            "platform_counts": {"aws": 50, "gcp": 25},
            "status_distribution": {"success": 60, "failure": 15},
        }

        # Set up mock response using set_post_response for filterPost
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            filter_data=list(raw_aggregations.items()),
            summary=raw_summary,
            total=75,
        )

        # Call the function
        result = await ols.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="platform=aws",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert result["summary"] == expected_result["summary"]
        filter_data = result["filterData"]
        assert isinstance(filter_data, list)
        assert len(filter_data) == len(expected_result["aggregation_keys"])
        # Convert filterData back to dict for easier verification
        filter_dict = dict(filter_data)
        for key in expected_result["aggregation_keys"]:
            assert key in filter_dict
        # Verify specific aggregation content
        assert filter_dict["benchmark"] == raw_aggregations["benchmark"]
        assert filter_dict["platform"] == raw_aggregations["platform"]
        assert filter_dict["jobStatus"] == raw_aggregations["jobStatus"]

    @pytest.mark.asyncio
    async def test_get_ols_filter_with_no_filter(self, fake_elastic_service):
        """Test getFilterData works correctly with no filter parameter."""
        # Raw aggregation data from Elasticsearch
        raw_aggregations = {
            "benchmark": [{"key": "ols-comprehensive-test", "doc_count": 25}],
            "workerNodesCount": [
                {"key": 4, "doc_count": 15},
                {"key": 8, "doc_count": 10},
            ],
            "olsTestWorkers": [
                {"key": 2, "doc_count": 12},
                {"key": 4, "doc_count": 13},
            ],
        }

        # Expected final result
        expected_result = {
            "total": 25,
            "filterData": raw_aggregations,
            "summary": {},
            "worker_counts": [4, 8],
            "test_worker_counts": [2, 4],
        }

        # Set up mock response
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            filter_data=list(raw_aggregations.items()),
            total=25,
        )

        # Call the function with empty filter
        result = await ols.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert result["total"] == expected_result["total"]
        assert result["filterData"] == list(raw_aggregations.items())
        assert result["summary"] == expected_result["summary"]
        # Verify worker count data is preserved
        filter_dict = dict(result["filterData"])
        assert filter_dict["workerNodesCount"] == raw_aggregations["workerNodesCount"]
        assert filter_dict["olsTestWorkers"] == raw_aggregations["olsTestWorkers"]

    @pytest.mark.asyncio
    async def test_get_ols_filter_empty_results(self, fake_elastic_service):
        """Test getFilterData handles empty OLS filter results gracefully."""
        # Expected result for empty data
        expected_result = {"total": 0, "filterData": [], "summary": {}}

        # Set up mock response for empty data
        fake_elastic_service.set_post_response(
            response_type="filterPost", filter_data=[], total=0
        )

        # Call the function
        result = await ols.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="platform=nonexistent",
            configpath="TEST",
        )

        # Verify empty results handling
        assert result["total"] == expected_result["total"]
        assert result["filterData"] == expected_result["filterData"]
        assert result["summary"] == expected_result["summary"]
        assert len(result["filterData"]) == 0

    @pytest.mark.asyncio
    async def test_get_ols_filter_complex_aggregations(self, fake_elastic_service):
        """Test getFilterData with complex OLS field aggregations."""
        # Complex aggregation data covering all OLS fields
        raw_aggregations = {
            "benchmark": [
                {"key": "ols-load-test", "doc_count": 35},
                {"key": "ols-stress-test", "doc_count": 25},
                {"key": "ols-endurance-test", "doc_count": 15},
            ],
            "releaseStream": [
                {"key": "4.15.0-0.nightly", "doc_count": 30},
                {"key": "4.14.5", "doc_count": 25},
                {"key": "4.13.8", "doc_count": 20},
            ],
            "platform": [
                {"key": "aws", "doc_count": 40},
                {"key": "azure", "doc_count": 20},
                {"key": "gcp", "doc_count": 15},
            ],
            "workerNodesCount": [
                {"key": 2, "doc_count": 15},
                {"key": 4, "doc_count": 35},
                {"key": 8, "doc_count": 25},
            ],
            "olsTestWorkers": [
                {"key": 1, "doc_count": 10},
                {"key": 2, "doc_count": 30},
                {"key": 4, "doc_count": 35},
            ],
            "olsTestDuration": [
                {"key": "short", "doc_count": 35},
                {"key": "medium", "doc_count": 25},
                {"key": "long", "doc_count": 15},
            ],
            "jobStatus": [
                {"key": "success", "doc_count": 65},
                {"key": "failure", "doc_count": 10},
            ],
        }

        # Comprehensive summary data
        raw_summary = {
            "totalTests": 75,
            "avgWorkers": 6.2,
            "avgDuration": 180.5,
            "successRate": 86.7,
            "avgNodesPerTest": 4.8,
        }

        # Expected final result with all OLS fields
        expected_result = {
            "total": 75,
            "filterData": raw_aggregations,
            "summary": raw_summary,
            "all_ols_fields": [
                "benchmark",
                "releaseStream",
                "platform",
                "workerNodesCount",
                "olsTestWorkers",
                "olsTestDuration",
                "jobStatus",
            ],
            "benchmark_variety": 3,
            "platform_variety": 3,
            "duration_categories": ["short", "medium", "long"],
            "worker_configurations": [2, 4, 8],
            "test_worker_configurations": [1, 2, 4],
        }

        # Set up mock response
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            filter_data=list(raw_aggregations.items()),
            summary=raw_summary,
            total=75,
        )

        # Call the function
        result = await ols.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 2, 1),
            filter="jobStatus=success&platform=aws",
            configpath="TEST",
        )

        # Verify results
        assert result["total"] == expected_result["total"]
        assert result["summary"] == expected_result["summary"]
        # Verify all OLS fields are present in filterData
        filter_dict = dict(result["filterData"])
        for field in expected_result["all_ols_fields"]:
            assert field in filter_dict
        # Verify specific field structures
        assert len(filter_dict["benchmark"]) == expected_result["benchmark_variety"]
        assert len(filter_dict["platform"]) == expected_result["platform_variety"]
        assert len(filter_dict["olsTestDuration"]) == len(
            expected_result["duration_categories"]
        )
        # Verify data integrity
        benchmark_keys = [item["key"] for item in filter_dict["benchmark"]]
        assert "ols-load-test" in benchmark_keys
        assert "ols-stress-test" in benchmark_keys
        assert "ols-endurance-test" in benchmark_keys


class TestOLSErrorHandling:
    """Test cases for error handling in OLS functions"""

    @pytest.mark.asyncio
    async def test_ols_index_not_found(self, fake_elastic_service):
        """Test OLS functions handle missing Elasticsearch index."""
        # Set up the service to raise an exception
        fake_elastic_service.set_post_response(
            response_type="filterPost", error=Exception("Index not found")
        )

        # Verify exception is raised
        with pytest.raises(Exception, match="Index not found"):
            await ols.getFilterData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                filter="platform=aws",
                configpath="TEST",
            )

    @pytest.mark.asyncio
    async def test_ols_elasticsearch_connection_error(self, fake_elastic_service):
        """Test OLS functions handle Elasticsearch connection errors."""
        # Set up the service to raise a connection exception
        fake_elastic_service.set_post_response(
            response_type="filterPost", error=Exception("Connection timeout")
        )

        # Verify exception is raised
        with pytest.raises(Exception, match="Connection timeout"):
            await ols.getFilterData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                filter="",
                configpath="TEST",
            )
