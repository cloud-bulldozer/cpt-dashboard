from fastapi import HTTPException
import pytest

from app.api.v1.commons import utils

"""Unit tests for the utils functions in the commons module.

Tests comprehensive utility functions used across the commons modules,
including data processing, query construction, filtering, and validation functions.
Follows established patterns from other commons tests with Given-When-Then structure.
"""


class TestJobDataProcessing:
    """Test cases for job data processing utility functions"""

    def test_update_status_lowercase_conversion(self):
        """Test updateStatus converts job status to lowercase."""
        # Given: A job with mixed case status
        job_data = {"jobStatus": "SUCCESS"}

        expected_result = {"status": "success", "conversion_applied": True}

        # When: updateStatus is called
        result = utils.updateStatus(job_data)

        # Then: Should return lowercase status
        assert result == expected_result["status"]

    def test_update_status_already_lowercase(self):
        """Test updateStatus handles already lowercase status."""
        # Given: A job with already lowercase status
        job_data = {"jobStatus": "failure"}

        expected_result = {"status": "failure", "no_change_needed": True}

        # When: updateStatus is called
        result = utils.updateStatus(job_data)

        # Then: Should return unchanged lowercase status
        assert result == expected_result["status"]

    def test_update_benchmark_with_upgrade_job(self):
        """Test updateBenchmark prefixes benchmark when upstreamJob contains 'upgrade'."""
        # Given: A job with upgrade in upstreamJob
        job_data = {
            "upstreamJob": "periodic-ci-openshift-upgrade-master",
            "benchmark": "cluster-density",
        }

        expected_result = {
            "benchmark": "upgrade-cluster-density",
            "prefix_applied": True,
        }

        # When: updateBenchmark is called
        result = utils.updateBenchmark(job_data)

        # Then: Should return prefixed benchmark
        assert result == expected_result["benchmark"]

    def test_update_benchmark_without_upgrade_job(self):
        """Test updateBenchmark returns original benchmark when no upgrade in upstreamJob."""
        # Given: A job without upgrade in upstreamJob
        job_data = {
            "upstreamJob": "periodic-ci-openshift-performance-master",
            "benchmark": "node-density",
        }

        expected_result = {"benchmark": "node-density", "no_prefix_needed": True}

        # When: updateBenchmark is called
        result = utils.updateBenchmark(job_data)

        # Then: Should return original benchmark
        assert result == expected_result["benchmark"]

    def test_job_type_periodic_detection(self):
        """Test jobType identifies periodic jobs correctly."""
        # Given: A job with periodic in upstreamJob
        job_data = {"upstreamJob": "periodic-ci-openshift-release-master-nightly-4.15"}

        expected_result = {"job_type": "periodic", "detection_correct": True}

        # When: jobType is called
        result = utils.jobType(job_data)

        # Then: Should return "periodic"
        assert result == expected_result["job_type"]

    def test_job_type_pull_request_detection(self):
        """Test jobType identifies pull request jobs correctly."""
        # Given: A job without periodic in upstreamJob
        job_data = {"upstreamJob": "pull-ci-openshift-release-master-ci-4.15"}

        expected_result = {"job_type": "pull request", "detection_correct": True}

        # When: jobType is called
        result = utils.jobType(job_data)

        # Then: Should return "pull request"
        assert result == expected_result["job_type"]

    def test_is_rehearse_true_detection(self):
        """Test isRehearse identifies rehearse jobs correctly."""
        # Given: A job with rehearse in upstreamJob
        job_data = {
            "upstreamJob": "periodic-ci-openshift-release-master-nightly-4.15-rehearse"
        }

        expected_result = {"is_rehearse": "True", "rehearse_detected": True}

        # When: isRehearse is called
        result = utils.isRehearse(job_data)

        # Then: Should return "True"
        assert result == expected_result["is_rehearse"]

    def test_is_rehearse_false_detection(self):
        """Test isRehearse identifies non-rehearse jobs correctly."""
        # Given: A job without rehearse in upstreamJob
        job_data = {"upstreamJob": "periodic-ci-openshift-release-master-nightly-4.15"}

        expected_result = {"is_rehearse": "False", "rehearse_not_detected": True}

        # When: isRehearse is called
        result = utils.isRehearse(job_data)

        # Then: Should return "False"
        assert result == expected_result["is_rehearse"]


class TestAWSJobClassification:
    """Test cases for AWS job classification logic"""

    def test_classify_rosa_hcp_job(self):
        """Test clasifyAWSJobs identifies ROSA HCP jobs correctly."""
        # Given: A job with rosa-hcp cluster type
        job_data = {
            "clusterType": "rosa-hcp",
            "masterNodesCount": 0,
            "infraNodesCount": 0,
            "platform": "aws",
        }

        expected_result = {
            "classification": "AWS ROSA-HCP",
            "rosa_hcp_identified": True,
        }

        # When: clasifyAWSJobs is called
        result = utils.clasifyAWSJobs(job_data)

        # Then: Should return "AWS ROSA-HCP"
        assert result == expected_result["classification"]

    def test_classify_rosa_job_with_zero_nodes(self):
        """Test clasifyAWSJobs identifies ROSA jobs with zero master/infra nodes."""
        # Given: A job with rosa in cluster type and zero master/infra nodes
        job_data = {
            "clusterType": "rosa",
            "masterNodesCount": 0,
            "infraNodesCount": 0,
            "platform": "aws",
        }

        expected_result = {
            "classification": "AWS ROSA-HCP",
            "rosa_zero_nodes_hcp": True,
        }

        # When: clasifyAWSJobs is called
        result = utils.clasifyAWSJobs(job_data)

        # Then: Should return "AWS ROSA-HCP"
        assert result == expected_result["classification"]

    def test_classify_rosa_job_with_nodes(self):
        """Test clasifyAWSJobs identifies regular ROSA jobs with nodes."""
        # Given: A job with rosa in cluster type but with master/infra nodes
        job_data = {
            "clusterType": "rosa",
            "masterNodesCount": 3,
            "infraNodesCount": 2,
            "platform": "aws",
        }

        expected_result = {
            "classification": "AWS ROSA",
            "regular_rosa_identified": True,
        }

        # When: clasifyAWSJobs is called
        result = utils.clasifyAWSJobs(job_data)

        # Then: Should return "AWS ROSA"
        assert result == expected_result["classification"]

    def test_classify_regular_aws_job(self):
        """Test clasifyAWSJobs returns platform for non-ROSA AWS jobs."""
        # Given: A regular AWS job without rosa in cluster type
        job_data = {
            "clusterType": "self-managed",
            "masterNodesCount": 3,
            "infraNodesCount": 2,
            "platform": "aws",
        }

        expected_result = {"classification": "aws", "platform_returned": True}

        # When: clasifyAWSJobs is called
        result = utils.clasifyAWSJobs(job_data)

        # Then: Should return original platform
        assert result == expected_result["classification"]


class TestBuildAndReleaseProcessing:
    """Test cases for build and release stream processing"""

    def test_get_build_extracts_correctly(self):
        """Test getBuild extracts build info by removing release stream."""
        # Given: A job with releaseStream and ocpVersion
        job_data = {
            "releaseStream": "4.15.0-0.nightly",
            "ocpVersion": "4.15.0-0.nightly-2024-01-15-123456",
        }

        expected_result = {"build": "2024-01-15-123456", "release_stream_removed": True}

        # When: getBuild is called
        result = utils.getBuild(job_data)

        # Then: Should return build without release stream prefix
        assert result == expected_result["build"]

    def test_get_build_with_different_format(self):
        """Test getBuild handles different version formats."""
        # Given: A job with different release stream format
        job_data = {"releaseStream": "4.14.5", "ocpVersion": "4.14.5-x86_64"}

        expected_result = {"build": "x86_64", "format_handled": True}

        # When: getBuild is called
        result = utils.getBuild(job_data)

        # Then: Should return correct build suffix
        assert result == expected_result["build"]

    def test_get_release_stream_fast_mapping(self):
        """Test getReleaseStream maps fast release stream correctly."""
        # Given: A row with fast release stream
        row_data = {"releaseStream": "4.15.0-0.fast-2024-01-15"}

        expected_result = {"release_stream": "Fast", "fast_mapped": True}

        # When: getReleaseStream is called
        result = utils.getReleaseStream(row_data)

        # Then: Should return mapped release stream
        assert result == expected_result["release_stream"]

    def test_get_release_stream_stable_default(self):
        """Test getReleaseStream defaults to Stable for unknown streams."""
        # Given: A row with unknown release stream
        row_data = {"releaseStream": "4.15.0-0.unknown-2024-01-15"}

        expected_result = {"release_stream": "Stable", "default_applied": True}

        # When: getReleaseStream is called
        result = utils.getReleaseStream(row_data)

        # Then: Should return default Stable
        assert result == expected_result["release_stream"]

    def test_build_release_stream_filter_with_duplicates(self):
        """Test buildReleaseStreamFilter maps and deduplicates release streams."""
        # Given: Input array with various release streams including duplicates
        input_array = [
            "4.15.0-0.fast-2024-01-15",
            "4.14.0-0.stable-2024-01-10",
            "4.15.0-0.fast-2024-01-16",  # Another fast (should deduplicate)
            "4.13.0-0.eus-2024-01-05",
            "unknown-format",
        ]

        expected_result = {
            "mapped_streams": ["Fast", "Stable", "EUS"],  # Deduplicated and mapped
            "deduplication_applied": True,
        }

        # When: buildReleaseStreamFilter is called
        result = utils.buildReleaseStreamFilter(input_array)

        # Then: Should return deduplicated mapped streams
        assert set(result) == set(expected_result["mapped_streams"])
        assert len(result) == len(expected_result["mapped_streams"])


class TestSortingAndPagination:
    """Test cases for sorting and pagination utilities"""

    def test_build_sort_terms_valid_input(self):
        """Test build_sort_terms creates correct sort structure."""
        # Given: Valid sort string
        sort_string = "startDate:desc"

        expected_result = {
            "sort_terms": [{"startDate": {"order": "desc"}}],
            "structure_correct": True,
        }

        # When: build_sort_terms is called
        result = utils.build_sort_terms(sort_string)

        # Then: Should return correct sort structure
        assert result == expected_result["sort_terms"]

    def test_build_sort_terms_empty_input(self):
        """Test build_sort_terms handles empty input."""
        # Given: Empty sort string
        sort_string = ""

        expected_result = {"sort_terms": [], "empty_handled": True}

        # When: build_sort_terms is called
        result = utils.build_sort_terms(sort_string)

        # Then: Should return empty list
        assert result == expected_result["sort_terms"]

    def test_build_sort_terms_invalid_direction(self):
        """Test build_sort_terms raises HTTPException for invalid direction."""
        # Given: Sort string with invalid direction
        sort_string = "startDate:invalid"

        # When: build_sort_terms is called with invalid direction
        # Then: Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            utils.build_sort_terms(sort_string)

        assert exc_info.value.status_code == 400

    def test_build_sort_terms_invalid_key(self):
        """Test build_sort_terms raises HTTPException for invalid key."""
        # Given: Sort string with invalid key
        sort_string = "invalidField:asc"

        # When: build_sort_terms is called with invalid key
        # Then: Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            utils.build_sort_terms(sort_string)

        assert exc_info.value.status_code == 400

    def test_normalize_pagination_both_none(self):
        """Test normalize_pagination handles both offset and size as None."""
        # Given: Both offset and size are None
        offset, size = None, None

        expected_result = {
            "offset": 0,
            "size": 10000,  # MAX_PAGE constant
            "defaults_applied": True,
        }

        # When: normalize_pagination is called
        result_offset, result_size = utils.normalize_pagination(offset, size)

        # Then: Should return defaults
        assert result_offset == expected_result["offset"]
        assert result_size == expected_result["size"]

    def test_normalize_pagination_offset_without_size(self):
        """Test normalize_pagination raises error when offset provided without size."""
        # Given: Offset provided without size
        offset, size = 100, None

        # When: normalize_pagination is called with offset but no size
        # Then: Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            utils.normalize_pagination(offset, size)

        assert exc_info.value.status_code == 400

    def test_normalize_pagination_offset_too_large(self):
        """Test normalize_pagination raises error when offset exceeds MAX_PAGE."""
        # Given: Offset exceeds MAX_PAGE
        offset, size = 15000, 100  # MAX_PAGE is 10000

        # When: normalize_pagination is called with oversized offset
        # Then: Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            utils.normalize_pagination(offset, size)

        assert exc_info.value.status_code == 400

    def test_normalize_pagination_valid_inputs(self):
        """Test normalize_pagination handles valid inputs correctly."""
        # Given: Valid offset and size
        offset, size = 50, 100

        expected_result = {"offset": 50, "size": 100, "inputs_preserved": True}

        # When: normalize_pagination is called
        result_offset, result_size = utils.normalize_pagination(offset, size)

        # Then: Should return unchanged values
        assert result_offset == expected_result["offset"]
        assert result_size == expected_result["size"]


class TestQueryConstruction:
    """Test cases for query construction utilities"""

    def test_build_aggregate_query_structure(self):
        """Test buildAggregateQuery creates correct aggregate structure."""
        # Given: Constant dictionary for aggregation
        constant_dict = {
            "platform": "platform.keyword",
            "benchmark": "benchmark.keyword",
            "jobStatus": "jobStatus.keyword",
        }

        expected_result = {
            "aggregate_structure": {
                "platform": {"terms": {"field": "platform.keyword"}},
                "benchmark": {"terms": {"field": "benchmark.keyword"}},
                "jobStatus": {"terms": {"field": "jobStatus.keyword"}},
            },
            "correct_structure": True,
        }

        # When: buildAggregateQuery is called
        result = utils.buildAggregateQuery(constant_dict)

        # Then: Should return correct aggregate structure
        assert result == expected_result["aggregate_structure"]

    def test_get_dict_from_qs_empty_input(self):
        """Test get_dict_from_qs handles empty query string."""
        # Given: Empty query string
        query_string = ""

        expected_result = {"result": {}, "empty_handled": True}

        # When: get_dict_from_qs is called
        result = utils.get_dict_from_qs(query_string)

        # Then: Should return empty dictionary
        assert result == expected_result["result"]

    def test_get_dict_from_qs_simple_params(self):
        """Test get_dict_from_qs parses simple query parameters."""
        # Given: Simple query string with parameters
        query_string = "platform=aws&benchmark=cluster-density&size=100"

        expected_result = {
            "result": {
                "platform": ["aws"],
                "benchmark": ["cluster-density"],
                "size": ["100"],
            },
            "simple_parsing": True,
        }

        # When: get_dict_from_qs is called
        result = utils.get_dict_from_qs(query_string)

        # Then: Should return parsed dictionary
        assert result == expected_result["result"]

    def test_get_dict_from_qs_with_list_values(self):
        """Test get_dict_from_qs handles list values in parameters."""
        # Given: Query string with list values
        query_string = "platform=['aws','gcp']&benchmark=node-density"

        expected_result = {
            "result": {"platform": ["aws", "gcp"], "benchmark": ["node-density"]},
            "list_values_parsed": True,
        }

        # When: get_dict_from_qs is called
        result = utils.get_dict_from_qs(query_string)

        # Then: Should return parsed list values
        assert result == expected_result["result"]

    def test_construct_query_single_value(self):
        """Test construct_query handles single values correctly."""
        # Given: Filter dictionary with single values
        filter_dict = {"cpu": ["intel"], "benchmark": ["cluster-density"]}

        expected_result = {
            "query": 'cpu="intel" test_type="cluster-density"',
            "single_values_formatted": True,
        }

        # When: construct_query is called
        result = utils.construct_query(filter_dict)

        # Then: Should return formatted query
        assert result == expected_result["query"]

    def test_construct_query_multiple_values(self):
        """Test construct_query handles multiple values with OR logic."""
        # Given: Filter dictionary with multiple values
        filter_dict = {"cpu": ["intel", "amd"], "benchmark": ["cluster-density"]}

        # When: construct_query is called
        result = utils.construct_query(filter_dict)

        # Then: Should return query with OR logic for multiple values
        assert 'cpu="intel" OR cpu="amd"' in result
        assert 'test_type="cluster-density"' in result

    def test_construct_query_release_stream_transformation(self):
        """Test construct_query transforms releaseStream values correctly."""
        # Given: Filter dictionary with releaseStream
        filter_dict = {"releaseStream": ["stable", "fast"]}

        # When: construct_query is called
        result = utils.construct_query(filter_dict)

        # Then: Should transform releaseStream with wildcards
        assert "*stable*" in result
        assert "*fast*" in result
        assert "ocp_build" in result  # Should use mapped field name

    def test_construct_query_status_mapping(self):
        """Test construct_query maps status values using TELCO_STATUS_MAP (lines 176-177)."""
        # Given: Filter dictionary with status values that need mapping
        filter_dict = {"jobStatus": ["success", "failed", "failure", "unknown_status"]}

        # When: construct_query is called
        result = utils.construct_query(filter_dict)

        # Then: Should apply TELCO_STATUS_MAP transformations (lines 176-177)
        assert 'status="passed"' in result  # "success" -> "passed"
        assert 'status="failed"' in result  # "failed" -> "failed"
        assert 'status="failure"' in result  # "failure" -> "failure"
        assert 'status="unknown_status"' in result  # unmapped stays same
        assert " OR " in result  # Multiple values should use OR logic

    def test_construct_query_non_dict_input(self):
        """Test construct_query when filter_dict is not a dict (line 172 false)."""
        # Given: Non-dictionary inputs that make isinstance(filter_dict, dict) False
        test_cases = [
            None,  # None value
            "string_input",  # String value
            ["list", "input"],  # List value
            42,  # Integer value
            True,  # Boolean value
        ]

        expected_result = {
            "return_value": None,
            "no_processing": True,
            "isinstance_false": True,
        }

        for filter_input in test_cases:
            # When: construct_query is called with non-dict input
            result = utils.construct_query(filter_input)

            # Then: Should return None since line 172 condition is False
            assert (
                result == expected_result["return_value"]
            ), f"Failed for input: {filter_input}"


class TestElasticsearchQueryConstruction:
    """Test cases for Elasticsearch-specific query construction"""

    def test_create_match_phrase_structure(self):
        """Test create_match_phrase creates correct Elasticsearch match phrase."""
        # Given: Key and item for match phrase
        key, item = "upstreamJob", "periodic"

        expected_result = {
            "match_phrase": {"match_phrase": {"upstreamJob": "periodic"}},
            "structure_correct": True,
        }

        # When: create_match_phrase is called
        result = utils.create_match_phrase(key, item)

        # Then: Should return correct match phrase structure
        assert result == expected_result["match_phrase"]

    def test_construct_es_filter_query_job_type_periodic(self):
        """Test construct_ES_filter_query handles jobType periodic correctly."""
        # Given: Filter with jobType periodic
        filter_dict = {"jobType": ["periodic"]}

        # When: construct_ES_filter_query is called
        result = utils.construct_ES_filter_query(filter_dict)

        # Then: Should place periodic in should_part
        assert len(result["query"]) == 1  # Should have one should clause
        assert len(result["must_query"]) == 0  # Must not should be empty for periodic
        assert result["min_match"] == 1

    def test_construct_es_filter_query_job_type_pull_request(self):
        """Test construct_ES_filter_query handles jobType pull request correctly."""
        # Given: Filter with jobType pull request (not periodic)
        filter_dict = {"jobType": ["pull request"]}

        # When: construct_ES_filter_query is called
        result = utils.construct_ES_filter_query(filter_dict)

        # Then: Should place periodic exclusion in must_not_part
        assert len(result["query"]) == 0  # Should part should be empty
        assert len(result["must_query"]) == 1  # Must not should have one clause
        assert result["min_match"] == 0  # Adjusted for must_not

    def test_construct_es_filter_query_is_rehearse_true(self):
        """Test construct_ES_filter_query handles isRehearse True correctly."""
        # Given: Filter with isRehearse True
        filter_dict = {"isRehearse": [True]}

        # When: construct_ES_filter_query is called
        result = utils.construct_ES_filter_query(filter_dict)

        # Then: Should place rehearse in should_part
        assert len(result["query"]) == 1
        assert result["query"][0]["match_phrase"]["upstreamJob"] == "rehearse"

    def test_construct_es_filter_query_is_rehearse_false(self):
        """Test construct_ES_filter_query handles isRehearse False correctly."""
        # Given: Filter with isRehearse False
        filter_dict = {"isRehearse": [False]}

        # When: construct_ES_filter_query is called
        result = utils.construct_ES_filter_query(filter_dict)

        # Then: Should place rehearse exclusion in must_not_part
        assert len(result["must_query"]) == 1
        assert result["must_query"][0]["match_phrase"]["upstreamJob"] == "rehearse"

    def test_construct_es_filter_query_result_failure(self):
        """Test construct_ES_filter_query handles result=failure correctly (lines 234-235)."""
        # Given: Filter with result=failure
        filter_dict = {"result": ["failure"]}

        # When: construct_ES_filter_query is called
        result = utils.construct_ES_filter_query(filter_dict)

        # Then: Should place failure in must_not_part (line 235)
        assert len(result["query"]) == 0  # should_part should be empty
        assert len(result["must_query"]) == 1  # must_not_part should have failure
        assert (
            result["must_query"][0]["match_phrase"]["result"] == "PASS"
        )  # search_value["result"] = "PASS"
        assert result["min_match"] == 0  # Adjusted for must_not

    def test_construct_es_filter_query_result_success(self):
        """Test construct_ES_filter_query handles result=success correctly (lines 234-235)."""
        # Given: Filter with result=success (not "failure")
        filter_dict = {"result": ["success"]}

        # When: construct_ES_filter_query is called
        result = utils.construct_ES_filter_query(filter_dict)

        # Then: Should place success in should_part (line 235 else clause)
        assert len(result["query"]) == 1  # should_part should have success
        assert len(result["must_query"]) == 0  # must_not_part should be empty
        assert (
            result["query"][0]["match_phrase"]["result"] == "PASS"
        )  # search_value["result"] = "PASS"
        assert result["min_match"] == 1

    def test_transform_filter_integration(self):
        """Test transform_filter integrates get_dict_from_qs and construct_ES_filter_query."""
        # Given: Query string filter
        filter_string = "jobType=periodic&platform=aws"

        # When: transform_filter is called
        result = utils.transform_filter(filter_string)

        # Then: Should return integrated result
        assert "query" in result
        assert "must_query" in result
        assert "min_match" in result
        assert isinstance(result["query"], list)
        assert isinstance(result["must_query"], list)


class TestProductFilterProcessing:
    """Test cases for product filter processing"""

    def test_update_filter_product_standout_products(self):
        """Test update_filter_product handles standout products correctly."""
        # Given: Filter with standout products
        filter_string = "product=['ocp','telco']&platform=aws"

        expected_result = {
            "filter_product": ["ocp", "telco"],
            "standout_products_identified": True,
            "filter_dict_product_empty": True,
        }

        # When: update_filter_product is called
        filter_product, filter_dict = utils.update_filter_product(filter_string)

        # Then: Should return standout products and clean filter dict
        assert filter_product == expected_result["filter_product"]
        assert "product" not in filter_dict or filter_dict["product"] == []
        assert "platform" in filter_dict

    def test_update_filter_product_general_products(self):
        """Test update_filter_product handles general products correctly."""
        # Given: Filter with general products (not standout)
        filter_string = "product=['Developer','Insights']&platform=aws"

        expected_result = {
            "filter_product": ["hce", "ocm"],  # GENERAL_PRODUCTS
            "general_products_mapped": True,
            "filter_dict_has_unmatched": True,
        }

        # When: update_filter_product is called
        filter_product, filter_dict = utils.update_filter_product(filter_string)

        # Then: Should map to general products and keep unmatched in filter_dict
        assert filter_product == expected_result["filter_product"]
        assert filter_dict["product"] == ["Developer", "Insights"]

    def test_update_filter_product_mixed_products(self):
        """Test update_filter_product handles mixed standout and general products."""
        # Given: Filter with both standout and general products
        filter_string = "product=['ocp','Developer','telco']"

        expected_result = {
            "filter_product": ["ocp", "telco", "hce", "ocm"],  # standout + general
            "mixed_products_handled": True,
        }

        # When: update_filter_product is called
        filter_product, filter_dict = utils.update_filter_product(filter_string)

        # Then: Should combine standout and general products
        assert set(filter_product) == set(expected_result["filter_product"])
        assert filter_dict["product"] == ["Developer"]  # unmatched kept in filter_dict

    def test_update_filter_product_no_product_filter(self):
        """Test update_filter_product handles filters without product."""
        # Given: Filter without product parameter
        filter_string = "platform=aws&benchmark=cluster-density"

        expected_result = {"filter_product": None, "no_product_handling": True}

        # When: update_filter_product is called
        filter_product, filter_dict = utils.update_filter_product(filter_string)

        # Then: Should return None for filter_product
        assert filter_product == expected_result["filter_product"]
        assert "platform" in filter_dict
        assert "benchmark" in filter_dict


class TestAsyncMetadataRetrieval:
    """Test cases for async metadata retrieval function"""

    @pytest.mark.asyncio
    async def test_get_metadata_successful_retrieval(self, fake_elastic):
        """Test getMetadata retrieves metadata successfully."""
        # Given: Elasticsearch response with metadata
        uuid = "test-uuid-12345"
        metadata = {
            "uuid": uuid,
            "test": "authentication_test",
            "group": "identity_mgmt",
            "result": "pass",
            "timestamp": "2024-01-15T10:30:00Z",
        }

        expected_result = {"metadata": metadata, "uuid_matched": True}

        # Set up mock response
        fake_elastic.set_post_response(
            response_type="post", data_list=[metadata], total=1
        )

        # When: getMetadata is called
        result = await utils.getMetadata(uuid=uuid, configpath="TEST")

        # Then: Should return metadata
        assert result == expected_result["metadata"]

    @pytest.mark.asyncio
    async def test_get_metadata_empty_response(self, fake_elastic):
        """Test getMetadata handles empty response gracefully."""
        # Given: Elasticsearch returns empty response
        uuid = "nonexistent-uuid"

        # Set up mock response with empty data
        fake_elastic.set_post_response(response_type="post", data_list=[], total=0)

        # When: getMetadata is called with nonexistent UUID
        # Then: Should raise IndexError since meta[0] won't exist
        with pytest.raises(IndexError):
            await utils.getMetadata(uuid=uuid, configpath="TEST")
