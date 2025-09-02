from datetime import date

import pandas as pd
import pytest

from app.api.v1.commons import ocp

"""Unit tests for the OCP (OpenShift Container Platform) data retrieval functions.

Tests the main OCP functions for getting data and filter data from Elasticsearch,
including various filtering, sorting, edge case scenarios, and DataFrame processing logic.
"""


class TestGetData:
    """Test cases for ocp.getData function"""

    @pytest.mark.asyncio
    async def test_get_ocp_results(self, fake_elastic):
        """Test getData returns OCP cluster results properly formatted."""
        # Raw source data from Elasticsearch
        raw_ocp_data = [
            {
                "timestamp": "2024-01-15T10:30:00.000Z",
                "ciSystem": "prow",
                "platform": "aws",
                "benchmark": "cluster-density-ms",
                "ocpVersion": "4.15.0-0.nightly-2024-01-14",
                "releaseStream": "4.15.0-0.nightly",
                "clusterType": "self-managed",
                "masterNodesCount": 3,
                "workerNodesCount": 120,
                "infraNodesCount": 3,
                "totalNodesCount": 126,
                "ipsec": "false",
                "fips": "false",
                "encrypted": "true",
                "encryptionType": "aes256",
                "publish": "external",
                "computeArch": "amd64",
                "controlPlaneArch": "amd64",
                "jobStatus": "success",
                "upstreamJob": "periodic-ci-openshift-release",
            },
            {
                "timestamp": "2024-01-16T14:20:00.000Z",
                "ciSystem": "prow",
                "platform": "gcp",
                "benchmark": "node-density-heavy",
                "ocpVersion": "4.14.5-x86_64",
                "releaseStream": "4.14.5",
                "clusterType": "self-managed",
                "masterNodesCount": 3,
                "workerNodesCount": 25,
                "infraNodesCount": None,
                "totalNodesCount": None,
                "ipsec": "",
                "fips": "",
                "encrypted": "false",
                "encryptionType": "",
                "publish": "",
                "computeArch": "",
                "controlPlaneArch": "",
                "jobStatus": "failure",
                "upstreamJob": "rehearse-12345-pull-request",
            },
        ]

        # Expected result after processing
        expected_result = {
            "total": 2,
            "timestamps": ["2024-01-15T10:30:00.000Z", "2024-01-16T14:20:00.000Z"],
            "platforms": [
                "aws",
                "gcp",
            ],  # clasifyAWSJobs returns original platform for self-managed
            "benchmarks": ["cluster-density-ms", "node-density-heavy"],
            "ocp_versions": ["4.15.0-0.nightly-2024-01-14", "4.14.5-x86_64"],
            "release_streams": ["4.15.0-0.nightly", "4.14.5"],
            "cluster_types": ["self-managed", "self-managed"],
            "master_node_counts": [3.0, 3.0],
            "worker_node_counts": [120.0, 25.0],
            "infra_node_counts": [3.0, 0.0],  # None becomes 0.0
            "total_node_counts": [126.0, 0.0],  # None becomes 0.0
            "encryption_types": ["aes256", "None"],  # processed by fillEncryptionType
            "short_versions": ["4.15", "4.14"],  # first 4 characters
            "job_statuses": ["success", "failure"],
            "na_fields": ["N/A", "N/A"],  # empty ipsec becomes N/A
        }

        # Set up mock response using set_post_response
        fake_elastic.set_post_response(
            response_type="post", data_list=raw_ocp_data, total=2
        )

        # Call the function
        result = await ocp.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            sort="startDate:desc",
            filter="platform=aws",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert isinstance(result["data"], pd.DataFrame)
        assert result["total"] == expected_result["total"]
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
        assert (
            result["data"]["encryptionType"].tolist()
            == expected_result["encryption_types"]
        )
        assert (
            result["data"]["shortVersion"].tolist() == expected_result["short_versions"]
        )
        assert result["data"]["jobStatus"].tolist() == expected_result["job_statuses"]
        assert (
            result["data"]["ipsec"].iloc[1] == expected_result["na_fields"][1]
        )  # Second item should be N/A

    @pytest.mark.asyncio
    async def test_get_ocp_empty_results(self, fake_elastic):
        """Test getData handles empty OCP results gracefully."""
        # Expected result for empty data
        expected_result = {"total": 0}

        # Set up mock response for empty results
        fake_elastic.set_post_response(response_type="post", data_list=[], total=0)

        # Call the function
        result = await ocp.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            sort=None,
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert isinstance(result["data"], pd.DataFrame)
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == 0

    @pytest.mark.asyncio
    async def test_get_ocp_filtered_platforms(self, fake_elastic):
        """Test getData filters out jobs with empty platforms."""
        # Raw data with some empty platforms (should be filtered out)
        raw_ocp_data = [
            {
                "timestamp": "2024-01-15T10:30:00.000Z",
                "platform": "aws",  # Valid platform
                "benchmark": "cluster-density-ms",
                "ocpVersion": "4.15.0-0.nightly",
                "releaseStream": "4.15.0-0.nightly",
                "clusterType": "self-managed",
                "masterNodesCount": 3,
                "workerNodesCount": 120,
                "infraNodesCount": 3,
                "totalNodesCount": 126,
                "ipsec": "false",
                "fips": "false",
                "encrypted": "true",
                "encryptionType": "aes256",
                "publish": "external",
                "computeArch": "amd64",
                "controlPlaneArch": "amd64",
                "jobStatus": "success",
                "upstreamJob": "periodic-ci-openshift-release",
            },
            {
                "timestamp": "2024-01-16T14:20:00.000Z",
                "platform": "",  # Empty platform - should be filtered out
                "benchmark": "node-density-heavy",
                "ocpVersion": "4.14.5-x86_64",
                "releaseStream": "4.14.5",
                "clusterType": "self-managed",
                "masterNodesCount": 3,
                "workerNodesCount": 25,
                "infraNodesCount": 3,
                "totalNodesCount": 31,
                "ipsec": "false",
                "fips": "false",
                "encrypted": "false",
                "encryptionType": "",
                "publish": "external",
                "computeArch": "amd64",
                "controlPlaneArch": "amd64",
                "jobStatus": "failure",
                "upstreamJob": "rehearse-12345-pull-request",
            },
        ]

        # Expected result - only valid platform jobs remain
        expected_result = {
            "total": 2,  # Total from ES response (before filtering)
            "data_length": 1,  # Actual data length after filtering
            "remaining_platform": "aws",
        }

        # Set up mock response
        fake_elastic.set_post_response(
            response_type="post", data_list=raw_ocp_data, total=2
        )

        # Call the function
        result = await ocp.getData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            size=10,
            offset=0,
            sort=None,
            filter="",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert isinstance(result["data"], pd.DataFrame)
        assert result["total"] == expected_result["total"]
        assert len(result["data"]) == expected_result["data_length"]
        assert (
            result["data"]["platform"].iloc[0] == expected_result["remaining_platform"]
        )


class TestGetFilterData:
    """Test cases for ocp.getFilterData function"""

    @pytest.mark.asyncio
    async def test_get_ocp_filter_data(self, fake_elastic):
        """Test getFilterData returns proper OCP filter aggregations."""
        # Raw aggregation data from Elasticsearch (formatted as list for filterData)
        raw_filter_data = [
            {
                "key": "platform",
                "value": [
                    {"key": "aws", "doc_count": 150},
                    {"key": "gcp", "doc_count": 75},
                ],
                "name": "Platform",
            },
            {
                "key": "benchmark",
                "value": [
                    {"key": "cluster-density-ms", "doc_count": 100},
                    {"key": "node-density-heavy", "doc_count": 125},
                ],
                "name": "Benchmark",
            },
        ]

        upstream_list = [
            "periodic-ci-openshift-release-master-nightly-4.15",
            "rehearse-12345-pull-request-test",
            "periodic-ci-openshift-performance-master",
        ]

        # Expected result after OCP filter processing
        expected_result = {
            "total": 225,
            "summary": {"totalJobs": 225},
            "job_types": ["periodic", "pull-request"],
            "rehearse_values": ["False", "True"],
            "filter_data_length": 4,  # Original 2 + jobType + isRehearse
        }

        # Set up mock response for filterPost
        fake_elastic.set_post_response(
            response_type="filterPost",
            total=225,
            filter_data=raw_filter_data,
            summary={"totalJobs": 225},
            upstream_list=upstream_list,
            repeat=1,
        )

        # Call the function
        result = await ocp.getFilterData(
            start_datetime=date(2024, 1, 1),
            end_datetime=date(2024, 1, 31),
            filter="platform=aws",
            configpath="TEST",
        )

        # Verify results
        assert isinstance(result, dict)
        assert result["total"] == expected_result["total"]
        assert result["summary"] == expected_result["summary"]
        assert len(result["filterData"]) == expected_result["filter_data_length"]

        # Check that jobType and isRehearse were added to filterData
        filter_data = result["filterData"]
        job_type_obj = next(
            (item for item in filter_data if item.get("key") == "jobType"), None
        )
        rehearse_obj = next(
            (item for item in filter_data if item.get("key") == "isRehearse"), None
        )

        assert job_type_obj is not None
        assert job_type_obj["name"] == "Job Type"
        assert set(job_type_obj["value"]) == set(expected_result["job_types"])

        assert rehearse_obj is not None
        assert rehearse_obj["name"] == "Rehearse"
        assert set(rehearse_obj["value"]) == set(expected_result["rehearse_values"])

    @pytest.mark.asyncio
    async def test_get_ocp_filter_data_empty(self, fake_elastic):
        """Test getFilterData handles empty results gracefully."""
        # Expected result for empty data
        expected_result = {"total": 0, "filterData": [], "summary": {}}

        # Set up mock response for empty results
        fake_elastic.set_post_response(
            response_type="filterPost", total=0, filter_data=[], summary={}
        )

        # Call the function
        result = await ocp.getFilterData(
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


class TestHelperFunctions:
    """Test cases for OCP helper functions"""

    def test_fill_encryption_type_with_na(self):
        """Test fillEncryptionType returns N/A when encrypted is N/A."""
        row = {"encrypted": "N/A", "encryptionType": "aes256"}
        expected_result = "N/A"

        result = ocp.fillEncryptionType(row)

        assert result == expected_result

    def test_fill_encryption_type_with_false(self):
        """Test fillEncryptionType returns None when encrypted is false."""
        row = {"encrypted": "false", "encryptionType": "aes256"}
        expected_result = "None"

        result = ocp.fillEncryptionType(row)

        assert result == expected_result

    def test_fill_encryption_type_with_true(self):
        """Test fillEncryptionType returns encryptionType when encrypted is true."""
        row = {"encrypted": "true", "encryptionType": "aes256"}
        expected_result = "aes256"

        result = ocp.fillEncryptionType(row)

        assert result == expected_result

    def test_get_job_type_periodic(self):
        """Test getJobType correctly identifies periodic jobs."""
        upstream_list = [
            "periodic-ci-openshift-release-master-nightly",
            "periodic-ci-openshift-performance-master",
        ]
        expected_result = ["periodic"]

        result = ocp.getJobType(upstream_list)

        assert result == expected_result

    def test_get_job_type_pull_request(self):
        """Test getJobType correctly identifies pull-request jobs."""
        upstream_list = ["rehearse-12345-some-test", "ci-op-some-pull-request"]
        expected_result = ["pull-request"]

        result = ocp.getJobType(upstream_list)

        assert result == expected_result

    def test_get_job_type_mixed(self):
        """Test getJobType handles mixed job types."""
        upstream_list = [
            "periodic-ci-openshift-release-master",
            "rehearse-54321-test-job",
            "periodic-ci-performance-test",
        ]
        expected_result = [
            "periodic",
            "pull-request",
        ]  # Set comprehension returns unique values

        result = ocp.getJobType(upstream_list)

        assert set(result) == set(expected_result)  # Order might vary in sets

    def test_get_is_rehearse_true(self):
        """Test getIsRehearse correctly identifies rehearse jobs."""
        upstream_list = ["rehearse-12345-some-test", "rehearse-67890-another-test"]
        expected_result = ["True"]

        result = ocp.getIsRehearse(upstream_list)

        assert result == expected_result

    def test_get_is_rehearse_false(self):
        """Test getIsRehearse correctly identifies non-rehearse jobs."""
        upstream_list = [
            "periodic-ci-openshift-release-master",
            "ci-op-some-pull-request",
        ]
        expected_result = ["False"]

        result = ocp.getIsRehearse(upstream_list)

        assert result == expected_result

    def test_get_is_rehearse_mixed(self):
        """Test getIsRehearse handles mixed rehearse and non-rehearse jobs."""
        upstream_list = [
            "periodic-ci-openshift-release-master",
            "rehearse-12345-test-job",
            "ci-op-pull-request-test",
        ]
        expected_result = ["True", "False"]  # Set comprehension returns unique values

        result = ocp.getIsRehearse(upstream_list)

        assert set(result) == set(expected_result)  # Order might vary in sets


class TestOCPErrorHandling:
    """Test cases for error handling in OCP functions"""

    @pytest.mark.asyncio
    async def test_get_data_elasticsearch_error(self, fake_elastic):
        """Test getData propagates Elasticsearch connection errors."""
        # Set up the service to raise an exception
        fake_elastic.set_post_response(
            "post", error=Exception("Elasticsearch unavailable")
        )

        # Verify exception is raised
        with pytest.raises(Exception, match="Elasticsearch unavailable"):
            await ocp.getData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                size=10,
                offset=0,
                sort=None,
                filter="",
                configpath="TEST",
            )

    @pytest.mark.asyncio
    async def test_get_filter_data_elasticsearch_error(self, fake_elastic):
        """Test getFilterData propagates Elasticsearch connection errors."""
        # Set up the service to raise an exception
        fake_elastic.set_post_response("filterPost", error=Exception("Index not found"))

        # Verify exception is raised
        with pytest.raises(Exception, match="Index not found"):
            await ocp.getFilterData(
                start_datetime=date(2024, 1, 1),
                end_datetime=date(2024, 1, 31),
                filter="",
                configpath="TEST",
            )
