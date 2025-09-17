from datetime import date

import pandas as pd
import pytest

from app.api.v1.commons import quay

"""Unit tests for the Quay (Container Registry) data retrieval functions.

Tests the main Quay functions for getting data and filter data from Elasticsearch,
including various filtering, data processing, and edge case scenarios using shared fixtures approach.
"""


class TestGetData:
    """Test cases for quay.getData function"""

    @pytest.mark.asyncio
    async def test_get_quay_results(self, fake_elastic_service):
        """Test getData returns Quay container registry results properly formatted."""
        # Raw source data from Elasticsearch
        raw_quay_data = [
            {
                "timestamp": "2024-01-15T10:30:00.000Z",
                "ciSystem": "prow",
                "platform": "aws",
                "benchmark": "quay-image-push-pull",
                "ocpVersion": "4.15.0-0.nightly-2024-01-14",
                "releaseStream": "4.15.0-0.nightly",
                "clusterType": "self-managed",
                "masterNodesCount": 3,
                "workerNodesCount": 5,
                "infraNodesCount": 2,
                "totalNodesCount": 10,
                "jobStatus": "success",
                "upstreamJob": "periodic-ci-quay-performance",
                "imagePushPulls": 1000,
                "concurrency": 10,
                "hitSize": 256,
            },
            {
                "timestamp": "2024-01-16T14:20:00.000Z",
                "ciSystem": "prow",
                "platform": "gcp",
                "benchmark": "quay-stress-test",
                "ocpVersion": "4.14.5-x86_64",
                "releaseStream": "4.14.5",
                "clusterType": "rosa-hcp",
                "masterNodesCount": 0,
                "workerNodesCount": 8,
                "infraNodesCount": None,
                "totalNodesCount": None,
                "jobStatus": "failure",
                "upstreamJob": "rehearse-12345-pull-request",
                "imagePushPulls": 500,
                "concurrency": 5,
                "hitSize": 128,
            },
        ]

        # Expected result after processing
        expected_result = {
            "total": 2,
            "timestamps": ["2024-01-15T10:30:00.000Z", "2024-01-16T14:20:00.000Z"],
            "platforms": ["aws", "AWS ROSA-HCP"],  # clasifyAWSJobs transforms rosa-hcp
            "benchmarks": ["quay-image-push-pull", "quay-stress-test"],
            "ocp_versions": ["4.15.0-0.nightly-2024-01-14", "4.14.5-x86_64"],
            "release_streams": ["4.15.0-0.nightly", "4.14.5"],
            "cluster_types": ["self-managed", "rosa-hcp"],
            "master_node_counts": [3.0, 0.0],
            "worker_node_counts": [5.0, 8.0],
            "infra_node_counts": [2.0, 0.0],  # None becomes 0.0
            "total_node_counts": [10.0, 0.0],  # None becomes 0.0
            "job_statuses": ["success", "failure"],
            "short_versions": ["4.15", "4.14"],  # first 4 characters
            "image_push_pulls": [1000, 500],
            "concurrency_levels": [10, 5],
            "hit_sizes": [256, 128],
        }

        # Set up mock response using set_post_response
        fake_elastic_service.set_post_response(
            response_type="post", data_list=raw_quay_data
        )

        # Call the function
        result = await quay.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            sort="startDate:desc",  # Use valid sort field from constants
            filter="platform=aws",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert isinstance(result["data"], pd.DataFrame)
        assert result["total"] == expected_result["total"]
        assert (
            len(result["data"]) == expected_result["total"]
        )  # Both platforms valid, no filtering
        assert result["data"]["timestamp"].tolist() == expected_result["timestamps"]
        assert result["data"]["platform"].tolist() == expected_result["platforms"]
        assert result["data"]["benchmark"].tolist() == expected_result["benchmarks"]
        assert result["data"]["ocpVersion"].tolist() == expected_result["ocp_versions"]
        assert (
            result["data"]["releaseStream"].tolist()
            == expected_result["release_streams"]
        )
        assert (
            result["data"]["clusterType"].tolist() == expected_result["cluster_types"]
        )
        assert (
            result["data"]["masterNodesCount"].tolist()
            == expected_result["master_node_counts"]
        )
        assert (
            result["data"]["workerNodesCount"].tolist()
            == expected_result["worker_node_counts"]
        )
        assert (
            result["data"]["infraNodesCount"].tolist()
            == expected_result["infra_node_counts"]
        )
        assert (
            result["data"]["totalNodesCount"].tolist()
            == expected_result["total_node_counts"]
        )
        assert result["data"]["jobStatus"].tolist() == expected_result["job_statuses"]
        assert (
            result["data"]["shortVersion"].tolist() == expected_result["short_versions"]
        )
        assert (
            result["data"]["imagePushPulls"].tolist()
            == expected_result["image_push_pulls"]
        )
        assert (
            result["data"]["concurrency"].tolist()
            == expected_result["concurrency_levels"]
        )
        assert result["data"]["hitSize"].tolist() == expected_result["hit_sizes"]

    @pytest.mark.asyncio
    async def test_get_quay_empty_results(self, fake_elastic_service):
        """Test getData handles empty Quay results gracefully."""
        # Expected result for empty data
        expected_result = {"total": 0, "data": pd.DataFrame()}

        # Set up mock response for empty data
        fake_elastic_service.set_post_response(response_type="post", data_list=[])

        # Call the function
        result = await quay.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            sort=None,
            filter="",
            configpath="TEST",
        )

        # Verify empty results handling
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == 0

    @pytest.mark.asyncio
    async def test_get_quay_filtered_platforms(self, fake_elastic_service):
        """Test getData filters out jobs with empty platforms."""
        # Raw data with some empty platforms (should be filtered out)
        raw_quay_data = [
            {
                "timestamp": "2024-01-15T10:30:00.000Z",
                "platform": "aws",  # Valid platform
                "benchmark": "quay-load-test",
                "ocpVersion": "4.15.0-0.nightly",
                "releaseStream": "4.15.0-0.nightly",
                "clusterType": "self-managed",
                "masterNodesCount": 3,
                "workerNodesCount": 5,
                "infraNodesCount": 2,
                "totalNodesCount": 10,
                "jobStatus": "success",
                "upstreamJob": "periodic-ci-quay-performance",
                "imagePushPulls": 800,
                "concurrency": 8,
                "hitSize": 192,
            },
            {
                "timestamp": "2024-01-16T14:20:00.000Z",
                "platform": "",  # Empty platform - should be filtered out
                "benchmark": "quay-performance-test",
                "ocpVersion": "4.14.5-x86_64",
                "releaseStream": "4.14.5",
                "clusterType": "self-managed",
                "masterNodesCount": 3,
                "workerNodesCount": 6,
                "infraNodesCount": 2,
                "totalNodesCount": 11,
                "jobStatus": "failure",
                "upstreamJob": "rehearse-12345-pull-request",
                "imagePushPulls": 400,
                "concurrency": 4,
                "hitSize": 96,
            },
        ]

        # Expected result - only valid platform jobs remain
        expected_result = {
            "total": 2,  # Total from ES response (before filtering)
            "data_length": 1,  # Actual data length after filtering
            "remaining_platform": "aws",
        }

        # Set up mock response
        fake_elastic_service.set_post_response(
            response_type="post", data_list=raw_quay_data
        )

        # Call the function
        result = await quay.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            sort=None,
            filter="",
            configpath="TEST",
        )

        # Verify platform filtering
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == expected_result["data_length"]
        assert (
            result["data"]["platform"].iloc[0] == expected_result["remaining_platform"]
        )

    @pytest.mark.asyncio
    async def test_get_quay_complex_processing(self, fake_elastic_service):
        """Test getData with complex Quay-specific data processing scenarios."""
        # Complex data testing various processing scenarios
        raw_quay_data = [
            {
                "timestamp": "2024-01-15T10:30:00.000Z",
                "ciSystem": "prow",
                "platform": "azure",
                "benchmark": "quay-concurrent-pulls",
                "ocpVersion": "4.13.8-multi-arch",
                "releaseStream": "4.13.8",
                "clusterType": "rosa",
                "masterNodesCount": 3,
                "workerNodesCount": 12,
                "infraNodesCount": 3,
                "totalNodesCount": 18,
                "jobStatus": "SUCCESS",  # Will be lowercased
                "upstreamJob": "periodic-ci-quay-scale-test",
                "imagePushPulls": 2000,
                "concurrency": 20,
                "hitSize": 512,
            },
            {
                "timestamp": "2024-01-16T11:45:00.000Z",
                "ciSystem": "jenkins",
                "platform": "baremetal",
                "benchmark": "quay-registry-stress",
                "ocpVersion": "4.12.15-stable",
                "releaseStream": "4.12.15",
                "clusterType": "self-managed",
                "masterNodesCount": 5,
                "workerNodesCount": 20,
                "infraNodesCount": 5,
                "totalNodesCount": 30,
                "jobStatus": "FAILED",  # Will be lowercased
                "upstreamJob": "release-4.12-pull-request-test",
                "imagePushPulls": 1500,
                "concurrency": 15,
                "hitSize": 384,
            },
        ]

        # Expected result with complex processing verification
        expected_result = {
            "total": 2,
            "complex_processing": {
                "status_lowercased": ["success", "failed"],  # updateStatus lowercases
                "rosa_classification": "AWS ROSA",  # clasifyAWSJobs for rosa
                "short_versions": ["4.13", "4.12"],
                "build_processing": True,  # getBuild function applied
                "benchmark_updated": True,  # updateBenchmark function applied
            },
            "quay_metrics": {
                "high_concurrency": 20,
                "high_image_ops": 2000,
                "large_hit_size": 512,
            },
        }

        # Set up mock response
        fake_elastic_service.set_post_response(
            response_type="post", data_list=raw_quay_data
        )

        # Call the function
        result = await quay.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 2, 1),
            size=20,
            offset=0,
            sort="workerNodesCount:desc",  # Use valid sort field from constants
            filter="concurrency>=15",
            configpath="TEST",
        )

        # Verify complex processing results
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == 2
        # Verify status processing (lowercased)
        assert (
            result["data"]["jobStatus"].tolist()
            == expected_result["complex_processing"]["status_lowercased"]
        )
        # Verify platform classification (rosa -> AWS ROSA)
        assert "AWS ROSA" in result["data"]["platform"].tolist()
        # Verify short version extraction
        assert (
            result["data"]["shortVersion"].tolist()
            == expected_result["complex_processing"]["short_versions"]
        )
        # Verify Quay-specific metrics are preserved
        assert (
            max(result["data"]["concurrency"])
            == expected_result["quay_metrics"]["high_concurrency"]
        )
        assert (
            max(result["data"]["imagePushPulls"])
            == expected_result["quay_metrics"]["high_image_ops"]
        )
        assert (
            max(result["data"]["hitSize"])
            == expected_result["quay_metrics"]["large_hit_size"]
        )


class TestGetFilterData:
    """Test cases for quay.getFilterData function"""

    @pytest.mark.asyncio
    async def test_get_quay_filter_aggregations(self, fake_elastic_service):
        """Test getFilterData returns proper Quay filter aggregations."""
        # Raw aggregation data from Elasticsearch
        raw_aggregations = {
            "benchmark": [
                {"key": "quay-image-push", "doc_count": 35},
                {"key": "quay-image-pull", "doc_count": 40},
                {"key": "quay-concurrent-ops", "doc_count": 25},
            ],
            "platform": [
                {"key": "aws", "doc_count": 50},
                {"key": "gcp", "doc_count": 30},
                {"key": "azure", "doc_count": 20},
            ],
            "releaseStream": [
                {"key": "4.15.0-0.nightly", "doc_count": 35},
                {"key": "4.14.5", "doc_count": 40},
                {"key": "4.13.8", "doc_count": 25},
            ],
            "jobStatus": [
                {"key": "success", "doc_count": 70},
                {"key": "failure", "doc_count": 30},
            ],
            "clusterType": [
                {"key": "self-managed", "doc_count": 60},
                {"key": "rosa-hcp", "doc_count": 25},
                {"key": "rosa", "doc_count": 15},
            ],
            "ciSystem": [
                {"key": "prow", "doc_count": 80},
                {"key": "jenkins", "doc_count": 20},
            ],
        }

        # Raw summary data from Elasticsearch
        raw_summary = {
            "totalTests": 100,
            "avgImageOps": 1250.5,
            "avgConcurrency": 12.3,
            "avgHitSize": 256.8,
        }

        # Expected final result after Quay filter processing
        expected_result = {
            "total": 100,
            "filterData": raw_aggregations,
            "summary": raw_summary,
            "quay_aggregation_keys": [
                "benchmark",
                "platform",
                "releaseStream",
                "jobStatus",
                "clusterType",
                "ciSystem",
            ],
            "benchmark_variety": 3,
            "platform_distribution": {"aws": 50, "gcp": 30, "azure": 20},
            "cluster_types": ["self-managed", "rosa-hcp", "rosa"],
            "ci_systems": ["prow", "jenkins"],
        }

        # Set up mock response using set_post_response for filterPost
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            filter_data=list(raw_aggregations.items()),
            summary=raw_summary,
            total=100,
        )

        # Call the function
        result = await quay.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="platform=aws&jobStatus=success",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert result["summary"] == expected_result["summary"]
        # Verify filterData structure and content
        filter_data = result["filterData"]
        assert isinstance(filter_data, list)
        assert len(filter_data) == len(expected_result["quay_aggregation_keys"])
        # Convert filterData back to dict for easier verification
        filter_dict = dict(filter_data)
        for key in expected_result["quay_aggregation_keys"]:
            assert key in filter_dict
        # Verify specific aggregation content
        assert filter_dict["benchmark"] == raw_aggregations["benchmark"]
        assert filter_dict["platform"] == raw_aggregations["platform"]
        assert filter_dict["jobStatus"] == raw_aggregations["jobStatus"]
        assert filter_dict["clusterType"] == raw_aggregations["clusterType"]

    @pytest.mark.asyncio
    async def test_get_quay_filter_with_no_filter(self, fake_elastic_service):
        """Test getFilterData works correctly with no filter parameter."""
        # Raw aggregation data from Elasticsearch focusing on Quay-specific fields
        raw_aggregations = {
            "imagePushPulls": [
                {"key": 500, "doc_count": 20},
                {"key": 1000, "doc_count": 35},
                {"key": 2000, "doc_count": 15},
            ],
            "concurrency": [
                {"key": 5, "doc_count": 25},
                {"key": 10, "doc_count": 30},
                {"key": 20, "doc_count": 15},
            ],
            "hitSize": [
                {"key": 128, "doc_count": 30},
                {"key": 256, "doc_count": 25},
                {"key": 512, "doc_count": 15},
            ],
            "workerNodesCount": [
                {"key": 3, "doc_count": 20},
                {"key": 5, "doc_count": 30},
                {"key": 10, "doc_count": 20},
            ],
        }

        # Expected final result
        expected_result = {
            "total": 70,
            "filterData": raw_aggregations,
            "summary": {},
            "quay_specific_fields": ["imagePushPulls", "concurrency", "hitSize"],
            "image_ops_range": [500, 1000, 2000],
            "concurrency_levels": [5, 10, 20],
            "hit_size_options": [128, 256, 512],
        }

        # Set up mock response
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            filter_data=list(raw_aggregations.items()),
            total=70,
        )

        # Call the function with empty filter
        result = await quay.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert result["total"] == expected_result["total"]
        assert result["filterData"] == list(raw_aggregations.items())
        assert result["summary"] == expected_result["summary"]
        # Verify Quay-specific field data is preserved
        filter_dict = dict(result["filterData"])
        for field in expected_result["quay_specific_fields"]:
            assert field in filter_dict
        # Verify range data integrity
        image_ops_keys = [item["key"] for item in filter_dict["imagePushPulls"]]
        assert set(image_ops_keys) == set(expected_result["image_ops_range"])

    @pytest.mark.asyncio
    async def test_get_quay_filter_empty_results(self, fake_elastic_service):
        """Test getFilterData handles empty Quay filter results gracefully."""
        # Expected result for empty data
        expected_result = {"total": 0, "filterData": [], "summary": {}}

        # Set up mock response for empty data
        fake_elastic_service.set_post_response(
            response_type="filterPost", filter_data=[], total=0
        )

        # Call the function
        result = await quay.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="platform=nonexistent&imagePushPulls>10000",
            configpath="TEST",
        )

        # Verify empty results handling
        assert result["total"] == expected_result["total"]
        assert result["filterData"] == expected_result["filterData"]
        assert result["summary"] == expected_result["summary"]
        assert len(result["filterData"]) == 0

    @pytest.mark.asyncio
    async def test_get_quay_filter_comprehensive_aggregations(
        self, fake_elastic_service
    ):
        """Test getFilterData with comprehensive Quay field aggregations."""
        # Comprehensive aggregation data covering all QUAY_FIELD_CONSTANT_DICT fields
        raw_aggregations = {
            "benchmark": [
                {"key": "quay-push-performance", "doc_count": 40},
                {"key": "quay-pull-latency", "doc_count": 30},
                {"key": "quay-registry-load", "doc_count": 30},
            ],
            "platform": [
                {"key": "aws", "doc_count": 50},
                {"key": "gcp", "doc_count": 25},
                {"key": "azure", "doc_count": 25},
            ],
            "releaseStream": [
                {"key": "4.15.0-0.nightly", "doc_count": 35},
                {"key": "4.14.5", "doc_count": 35},
                {"key": "4.13.8", "doc_count": 30},
            ],
            "workerNodesCount": [
                {"key": 3, "doc_count": 25},
                {"key": 5, "doc_count": 40},
                {"key": 10, "doc_count": 35},
            ],
            "jobStatus": [
                {"key": "success", "doc_count": 80},
                {"key": "failure", "doc_count": 20},
            ],
            "build": [  # Maps to ocpVersion.keyword
                {"key": "4.15.0-0.nightly-2024-01-14", "doc_count": 35},
                {"key": "4.14.5-x86_64", "doc_count": 35},
                {"key": "4.13.8-multi", "doc_count": 30},
            ],
            "upstream": [  # Maps to upstreamJob.keyword
                {"key": "periodic-ci-quay-performance", "doc_count": 50},
                {"key": "rehearse-12345-pull-request", "doc_count": 30},
                {"key": "release-4.15-quay-test", "doc_count": 20},
            ],
            "clusterType": [
                {"key": "self-managed", "doc_count": 60},
                {"key": "rosa-hcp", "doc_count": 25},
                {"key": "rosa", "doc_count": 15},
            ],
            "ciSystem": [
                {"key": "prow", "doc_count": 85},
                {"key": "jenkins", "doc_count": 15},
            ],
            "imagePushPulls": [
                {"key": 500, "doc_count": 20},
                {"key": 1000, "doc_count": 40},
                {"key": 2000, "doc_count": 25},
                {"key": 5000, "doc_count": 15},
            ],
            "concurrency": [
                {"key": 1, "doc_count": 15},
                {"key": 5, "doc_count": 25},
                {"key": 10, "doc_count": 35},
                {"key": 20, "doc_count": 25},
            ],
            "hitSize": [
                {"key": 64, "doc_count": 20},
                {"key": 128, "doc_count": 30},
                {"key": 256, "doc_count": 30},
                {"key": 512, "doc_count": 20},
            ],
        }

        # Comprehensive summary data
        raw_summary = {
            "totalTests": 100,
            "avgImageOps": 1875.5,
            "avgConcurrency": 11.8,
            "avgHitSize": 247.5,
            "successRate": 80.0,
            "avgWorkerNodes": 6.2,
        }

        # Expected final result with all Quay fields
        expected_result = {
            "total": 100,
            "filterData": raw_aggregations,
            "summary": raw_summary,
            "all_quay_fields": [
                "benchmark",
                "platform",
                "releaseStream",
                "workerNodesCount",
                "jobStatus",
                "build",
                "upstream",
                "clusterType",
                "ciSystem",
                "imagePushPulls",
                "concurrency",
                "hitSize",
            ],
            "quay_specific_metrics": ["imagePushPulls", "concurrency", "hitSize"],
            "field_count": 12,
            "image_ops_variety": 4,
            "concurrency_variety": 4,
            "hit_size_variety": 4,
        }

        # Set up mock response
        fake_elastic_service.set_post_response(
            response_type="filterPost",
            filter_data=list(raw_aggregations.items()),
            summary=raw_summary,
            total=100,
        )

        # Call the function
        result = await quay.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 2, 1),
            filter="jobStatus=success&platform=aws&concurrency>=5",
            configpath="TEST",
        )

        # Verify comprehensive results
        assert result["total"] == expected_result["total"]
        assert result["summary"] == expected_result["summary"]
        # Verify all Quay fields are present in filterData
        filter_dict = dict(result["filterData"])
        for field in expected_result["all_quay_fields"]:
            assert field in filter_dict
        # Verify Quay-specific metric fields have proper variety
        assert (
            len(filter_dict["imagePushPulls"]) == expected_result["image_ops_variety"]
        )
        assert len(filter_dict["concurrency"]) == expected_result["concurrency_variety"]
        assert len(filter_dict["hitSize"]) == expected_result["hit_size_variety"]
        # Verify field count matches expectation
        assert len(filter_dict) == expected_result["field_count"]
        # Verify data integrity for key Quay metrics
        image_ops_values = [item["key"] for item in filter_dict["imagePushPulls"]]
        assert 5000 in image_ops_values  # Highest value present
        assert 500 in image_ops_values  # Lowest value present


class TestQuayErrorHandling:
    """Test cases for error handling in Quay functions"""

    @pytest.mark.asyncio
    async def test_quay_index_not_found(self, fake_elastic_service):
        """Test Quay functions handle missing Elasticsearch index."""
        # Set up the service to raise an exception for getData
        fake_elastic_service.set_post_response(
            response_type="post", error=Exception("Index not found")
        )

        # Verify exception is raised for getData
        with pytest.raises(Exception, match="Index not found"):
            await quay.getData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                size=10,
                offset=0,
                sort="startDate:desc",  # Use valid sort field from constants
                filter="platform=aws",
                configpath="TEST",
            )

    @pytest.mark.asyncio
    async def test_quay_elasticsearch_connection_error(self, fake_elastic_service):
        """Test Quay functions handle Elasticsearch connection errors."""
        # Set up the service to raise a connection exception for getFilterData
        fake_elastic_service.set_post_response(
            response_type="filterPost", error=Exception("Connection timeout")
        )

        # Verify exception is raised for getFilterData
        with pytest.raises(Exception, match="Connection timeout"):
            await quay.getFilterData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                filter="imagePushPulls>1000",
                configpath="TEST",
            )
