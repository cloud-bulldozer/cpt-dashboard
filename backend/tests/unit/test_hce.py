from datetime import date

import pandas as pd
import pytest

from app.api.v1.commons import hce

"""Unit tests for the HCE (Hybrid Cloud Experience) data retrieval functions.

Tests the main HCE functions for getting data and filter data from Elasticsearch,
including various filtering and edge case scenarios using shared fixtures approach.
"""


class TestGetData:
    """Test cases for hce.getData function"""

    @pytest.mark.asyncio
    async def test_get_hce_results(self, fake_elastic_service):
        """Test getData returns HCE test results properly formatted."""
        # Raw source data from Elasticsearch
        raw_hce_data = [
            {
                "test": "authentication_test",
                "group": "identity_mgmt",
                "result": "pass",
                "date": "2024-01-15",
            },
            {
                "test": "database_connection_test",
                "group": "data_layer",
                "result": "fail",
                "date": "2024-01-16",
            },
        ]

        # Expected final result after HCE processing
        expected_result = {"data": pd.DataFrame(raw_hce_data).fillna(""), "total": 2}

        # Set up mock response using set_post_response
        fake_elastic_service.set_post_response(
            response_type="post", data_list=raw_hce_data
        )

        # Call the function
        result = await hce.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            filter="group=identity_mgmt",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == len(expected_result["data"])
        assert result["data"].to_dict("records") == expected_result["data"].to_dict(
            "records"
        )

    @pytest.mark.asyncio
    async def test_get_hce_empty_results(self, fake_elastic_service):
        """Test getData handles empty HCE results gracefully."""
        # Empty raw data from Elasticsearch
        raw_hce_data = []

        # Expected final result after HCE processing
        expected_result = {"data": pd.DataFrame(raw_hce_data).fillna(""), "total": 0}

        # Set up mock response for empty results using set_post_response
        fake_elastic_service.set_post_response(response_type="post", data_list=[])

        # Call the function
        result = await hce.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == len(expected_result["data"])
        assert result["data"].to_dict("records") == expected_result["data"].to_dict(
            "records"
        )

    @pytest.mark.asyncio
    async def test_get_hce_nan_group_handling(self, fake_elastic_service):
        """Test getData properly handles null group values in HCE data."""
        # Raw data with null group from Elasticsearch
        raw_hce_data = [{"test": "orphaned_test", "group": None, "result": "pass"}]

        # Expected final result after HCE processing (group NaN filled with 0)
        expected_result = {
            "data": pd.DataFrame(
                [{"test": "orphaned_test", "group": 0, "result": "pass"}]
            ).fillna(""),
            "total": 1,
        }

        # Set up mock response with null group using set_post_response
        fake_elastic_service.set_post_response(
            response_type="post", data_list=raw_hce_data
        )

        # Call the function
        result = await hce.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == len(expected_result["data"])
        assert result["data"].to_dict("records") == expected_result["data"].to_dict(
            "records"
        )


class TestGetFilterData:
    """Test cases for hce.getFilterData function"""

    @pytest.mark.asyncio
    async def test_get_hce_filter_aggregations(self, fake_elastic_service):
        """Test getFilterData returns proper HCE filter aggregations."""
        # Raw aggregation data from Elasticsearch
        raw_aggregations = {
            "testName": [
                {"key": "authentication_test", "doc_count": 25},
                {"key": "database_test", "doc_count": 15},
            ],
            "product": [
                {"key": "identity_service", "doc_count": 30},
                {"key": "data_service", "doc_count": 10},
            ],
        }

        # Expected final result after HCE filter processing
        expected_result = {"total": 0, "filterData": raw_aggregations, "summary": {}}

        # Set up mock response for filterPost using set_post_response
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            total=0,
            filter_data=raw_aggregations,
            summary={},
        )

        # Call the function
        result = await hce.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="group=identity_service",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert result["filterData"] == expected_result["filterData"]
        assert result["summary"] == expected_result["summary"]

    @pytest.mark.asyncio
    async def test_get_hce_filter_no_filter(self, fake_elastic_service):
        """Test getFilterData works without filters for HCE data."""
        # Raw aggregation data from Elasticsearch
        raw_aggregations = {
            "result": [
                {"key": "pass", "doc_count": 80},
                {"key": "fail", "doc_count": 20},
            ]
        }

        # Expected final result after HCE filter processing
        expected_result = {"total": 0, "filterData": raw_aggregations, "summary": {}}

        # Set up mock response for filterPost using set_post_response
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            total=0,
            filter_data=raw_aggregations,
            summary={},
        )

        # Call the function
        result = await hce.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert result["filterData"] == expected_result["filterData"]
        assert result["summary"] == expected_result["summary"]


class TestHCEErrorHandling:
    """Test cases for error handling in HCE functions"""

    @pytest.mark.asyncio
    async def test_hce_index_not_found(self, fake_elastic_service):
        """Test HCE functions handle missing Elasticsearch index."""
        # Set up the service to raise an exception
        fake_elastic_service.set_post_response(
            response_type="post", error=Exception("Index not found")
        )

        # Verify exception is raised
        with pytest.raises(Exception, match="Index not found"):
            await hce.getData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                size=10,
                offset=0,
                filter="",
                configpath="TEST",
            )

    @pytest.mark.asyncio
    async def test_hce_filter_index_not_found(self, fake_elastic_service):
        """Test getFilterData handles missing Elasticsearch index."""
        # Set up the service to raise an exception
        fake_elastic_service.set_post_response(
            response_type="filterPost", error=Exception("Index not found")
        )

        # Verify exception is raised
        with pytest.raises(Exception, match="Index not found"):
            await hce.getFilterData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                filter="",
                configpath="TEST",
            )
