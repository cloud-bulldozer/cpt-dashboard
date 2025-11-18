from datetime import datetime
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from vyper import Vyper

from app.services.search import (
    buildPlatformFilter,
    ElasticService,
    flatten_dict,
    getBuildFilter,
    IndexTimestamp,
    removeKeys,
    SortedIndexList,
)

"""Unit tests for ElasticService.

Assisted-by: Cursor / claude-4-5-sonnet-20240620

These tests are designed to cover the ElasticService class and its methods.

Cursor had trouble understanding how to mock the config object. I had to
rewrite the tests to use the monkeypatch fixture (maybe only because I wasn't
sufficiently familiar with the `@patch` decorator to figure out how to fix the
problem).

There were a few additional issues that I had to fix, due to more subtle
misunderstandings of the logic.

The resulting coverage is only 76%, largely because Cursor didn't understand
the odd behavior of the `post` method with both "new" and "prev" elasticsearch
clients. Having already spent more time than planned on this, I'm going to
create a follow-on Jira ticket to complete the coverage later.
"""


@pytest.fixture
def mock_config(monkeypatch):
    """Mock configuration for testing"""
    v = Vyper()
    monkeypatch.setattr("app.config.get_config", lambda: v)
    return v


@pytest.fixture
def mock_config_full(mock_config):
    mock_config.set_config_type("yaml")
    mock_config.read_config(
        json.dumps(
            {
                "elasticsearch": {
                    "url": "http://localhost:9200",
                    "indice": "test-index",
                    "username": "testuser",
                    "password": "testpass",
                    "prefix": "test-",
                    "internal": {
                        "url": "http://internal:9200",
                        "indice": "internal-index",
                        "username": "internal-user",
                        "password": "internal-pass",
                        "prefix": "internal-",
                    },
                },
            }
        )
    )
    return mock_config


@pytest.fixture
def mock_config_no_internal(mock_config):
    """Mock configuration without internal elasticsearch"""
    mock_config.set_config_type("yaml")
    mock_config.read_config(
        json.dumps(
            {
                "elasticsearch": {
                    "url": "http://localhost:9200",
                    "indice": "test-index",
                    "prefix": "test-",
                },
            }
        )
    )
    return mock_config


@pytest.fixture
def mock_config_no_auth(mock_config):
    """Mock configuration without authentication"""
    mock_config.set_config_type("yaml")
    mock_config.read_config(
        json.dumps(
            {"elasticsearch": {"url": "http://localhost:9200", "indice": "test-index"}}
        )
    )
    return mock_config


class TestElasticService:
    """Test class for ElasticService"""

    @patch("app.services.search.AsyncOpenSearch")
    def test_init_with_internal(self, mock_es, mock_config_full):
        """Test ElasticService initialization with internal elasticsearch"""

        service = ElasticService("elasticsearch")

        assert service.new_es is not None
        assert service.prev_es is not None
        assert service.new_index == "test-index"
        assert service.new_index_prefix == "test-"
        assert service.prev_index == "internal-index"
        assert service.prev_index_prefix == "internal-"

    @patch("app.services.search.AsyncOpenSearch")
    def test_init_without_internal(self, mock_es, mock_config_no_internal):
        """Test ElasticService initialization without internal elasticsearch"""

        service = ElasticService("elasticsearch")

        assert service.new_es is not None
        assert service.prev_es is None

    @patch("app.services.search.AsyncOpenSearch")
    def test_initialize_es_with_auth(self, mock_es, mock_config_full):
        """Test initialize_es method with authentication"""

        service = ElasticService("elasticsearch")
        es, indice, prefix = service.initialize_es(
            mock_config_full, "elasticsearch", ""
        )

        mock_es.assert_called_with(
            "http://localhost:9200",
            verify_certs=False,
            http_auth=("testuser", "testpass"),
        )
        assert indice == "test-index"
        assert prefix == "test-"

    @patch("app.services.search.AsyncOpenSearch")
    def test_initialize_es_without_auth(self, mock_es, mock_config_no_auth):
        """Test initialize_es method without authentication"""

        service = ElasticService("elasticsearch")
        es, indice, prefix = service.initialize_es(
            mock_config_no_auth, "elasticsearch", "custom-index"
        )

        mock_es.assert_called_with("http://localhost:9200", verify_certs=False)
        assert indice == "custom-index"
        assert prefix == ""

    @patch("app.services.search.AsyncOpenSearch")
    @patch("app.services.search.jsonable_encoder")
    async def test_post_aggregation_query(
        self, mock_encoder, mock_es, mock_config_full
    ):
        """Test post method with aggregation query (size=0)"""

        mock_es_instance = AsyncMock()
        mock_es.return_value = mock_es_instance
        mock_response = {"aggregations": {"test": "result"}}
        mock_es_instance.search.return_value = mock_response
        mock_encoder.return_value = {"query": "test"}

        service = ElasticService("elasticsearch")
        query = {"aggs": {"test": {"terms": {"field": "status"}}}}

        result = await service.post(query, size=0)

        assert result == mock_response
        mock_es_instance.search.assert_called_once_with(
            index="internal-internal-index*", body=query, size=0
        )

    @patch("app.services.search.AsyncOpenSearch")
    @patch("app.services.search.datetime")
    async def test_post_with_timestamp_field(
        self, mock_datetime, mock_es, mock_config_full
    ):
        """Test post method with timestamp field"""
        # Mock datetime.today()
        mock_today = datetime(2024, 1, 10).date()
        mock_datetime.today.return_value = Mock(date=Mock(return_value=mock_today))

        mock_config = Mock()
        mock_config.get.side_effect = lambda key: {
            "elasticsearch.url": "http://localhost:9200",
            "elasticsearch.indice": "test-index",
            "elasticsearch.internal.url": "http://internal:9200",
            "elasticsearch.internal.indice": "internal-index",
        }.get(key)

        mock_es_instance = AsyncMock()
        mock_es.return_value = mock_es_instance
        mock_response = {
            "hits": {"hits": [{"_source": {"test": "data"}}], "total": {"value": 1}}
        }
        mock_es_instance.search.return_value = mock_response

        service = ElasticService("elasticsearch")
        # Mock both new_es and prev_es
        service.prev_es = mock_es_instance

        query = {"query": {"bool": {"filter": {"range": {"timestamp": {}}}}}}

        start_date = datetime(2024, 1, 1).date()
        end_date = datetime(2024, 1, 5).date()

        result = await service.post(
            query, timestamp_field="timestamp", start_date=start_date, end_date=end_date
        )

        assert "data" in result
        assert "total" in result

    @patch("app.services.search.AsyncOpenSearch")
    async def test_post_without_timestamp_field(self, mock_es, mock_config_no_internal):
        """Test post method without timestamp field"""

        mock_es_instance = AsyncMock()
        mock_es.return_value = mock_es_instance
        mock_response = {
            "hits": {"hits": [{"_source": {"test": "data"}}], "total": {"value": 1}}
        }
        mock_es_instance.search.return_value = mock_response

        service = ElasticService("elasticsearch")
        query = {"query": {"match_all": {}}}

        result = await service.post(query)
        assert result["data"] == [{"_source": {"test": "data"}}]
        assert result["total"] == 1

    async def test_remove_duplicates(self, mock_config):
        """Test remove_duplicates method"""
        service = ElasticService()
        test_data = [
            {"_source": {"id": 1, "name": "test1"}},
            {"_source": {"id": 2, "name": "test2"}},
            {"_source": {"id": 1, "name": "test1"}},  # Duplicate
            {"_source": {"id": 3, "name": "test3"}},
        ]

        result = await service.remove_duplicates(test_data)

        assert len(result) == 3
        unique_ids = [item["_source"]["id"] for item in result]
        assert sorted(unique_ids) == [1, 2, 3]

    def test_get_unique_values(self, mock_config):
        """Test get_unique_values method"""
        service = ElasticService()
        test_values = ["Test", "test", "OTHER", "other", "NEW"]

        result = service.get_unique_values(test_values)

        assert len(result) == 3
        assert "Test" in result
        assert "OTHER" in result
        assert "NEW" in result

    @patch(
        "app.services.search.constants.JOB_STATUS_MAP",
        {"pass": "success", "fail": "failure"},
    )
    @patch(
        "app.services.search.constants.FILEDS_DISPLAY_NAMES",
        {"result": "Status", "platform": "Platform", "ocpVersion": "OCP Version"},
    )
    @patch("app.services.search.constants.OCP_SHORT_VER_LEN", 4)
    async def test_buildFilterData(self, mock_config_no_internal):
        """Test buildFilterData method"""
        service = ElasticService("elasticsearch")

        filter_data = {
            "result": {
                "buckets": [
                    {"key": "pass", "doc_count": 10},
                    {"key": "fail", "doc_count": 5},
                ]
            },
            "platform": {
                "buckets": [
                    {"key": "aws", "doc_count": 8},
                    {"key": "gcp", "doc_count": 7},
                ]
            },
            "ocpVersion": {
                "buckets": [
                    {"key": "4.14.1-rc.1", "doc_count": 5},
                    {"key": "4.14.2-rc.1", "doc_count": 3},
                ]
            },
            "upstream": {"buckets": []},
            "clusterType": {"buckets": []},
        }

        result = await service.buildFilterData(filter_data, 15)
        assert "filterData" in result
        assert "summary" in result
        assert "upstreamList" in result

        # Check that job status mapping worked
        filter_items = {item["key"]: item for item in result["filterData"]}
        assert "jobStatus" in filter_items
        assert "success" in filter_items["jobStatus"]["value"]
        assert "failure" in filter_items["jobStatus"]["value"]

        # Check OCP version shortening
        assert "ocpVersion" in filter_items
        assert "4.14" in filter_items["ocpVersion"]["value"]

    async def test_getSummary(self, mock_config):
        """Test getSummary method"""
        service = ElasticService()

        filter_data = {
            "result": {
                "buckets": [
                    {"key": "pass", "doc_count": 10},
                    {"key": "fail", "doc_count": 5},
                    {"key": "other", "doc_count": 2},
                ]
            }
        }

        with patch(
            "app.services.search.constants.JOB_STATUS_MAP",
            {"pass": "success", "fail": "failure", "other": "other"},
        ):
            result = await service.getSummary(filter_data, 17)

        assert result["total"] == 17
        assert result["success"] == 10
        assert result["failure"] == 5
        assert result["other"] == 2

    async def test_buildFilterValues(self, mock_config):
        """Test buildFilterValues method"""
        service = ElasticService()

        filter_data = {
            "build": {
                "buckets": [
                    {"key": "test-job-build-4.14.1-rc.1"},
                    {"key": "another-job-build-4.15.0-rc.2"},
                ]
            }
        }

        with patch("app.services.search.getBuildFilter") as mock_get_build_filter:
            mock_get_build_filter.return_value = ["4.14.1-rc.1", "4.15.0-rc.2"]

            result = await service.buildFilterValues(filter_data)

            assert result["key"] == "build"
            assert result["name"] == "Build"
            assert result["value"] == ["4.14.1-rc.1", "4.15.0-rc.2"]

    @patch("app.services.search.datetime")
    async def test_buildFilterQuery(self, mock_datetime, mock_config):
        """Test buildFilterQuery method"""
        service = ElasticService()

        # Mock datetime.utcnow()
        mock_now = datetime(2024, 1, 10, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        start_datetime = datetime(2024, 1, 1)
        end_datetime = datetime(2024, 1, 5)
        aggregate = {"status": {"terms": {"field": "status"}}}
        refiner = {
            "query": [{"term": {"platform": "aws"}}],
            "min_match": 1,
            "must_query": [{"term": {"status": "failed"}}],
        }

        result = await service.buildFilterQuery(
            start_datetime, end_datetime, aggregate, refiner, "timestamp"
        )

        assert "aggs" in result
        assert "query" in result
        assert result["aggs"] == aggregate
        assert "bool" in result["query"]
        assert "filter" in result["query"]["bool"]
        assert "range" in result["query"]["bool"]["filter"]
        assert "timestamp" in result["query"]["bool"]["filter"]["range"]
        assert result["query"]["bool"]["should"] == refiner["query"]
        assert result["query"]["bool"]["minimum_should_match"] == refiner["min_match"]
        assert result["query"]["bool"]["must_not"] == refiner["must_query"]

    def test_merge_aggregations(self, mock_config):
        """Test merge_aggregations method"""
        service = ElasticService()

        agg1 = {
            "status": {
                "buckets": [
                    {"key": "success", "doc_count": 10},
                    {"key": "failure", "doc_count": 5},
                ]
            },
            "total": {"value": 15},
        }

        agg2 = {
            "status": {
                "buckets": [
                    {"key": "success", "doc_count": 8},
                    {"key": "pending", "doc_count": 3},
                ]
            },
            "total": {"value": 11},
            "platform": {"buckets": [{"key": "aws", "doc_count": 7}]},
        }

        result = service.merge_aggregations(agg1, agg2)

        assert result["total"]["value"] == 26
        assert len(result["status"]["buckets"]) == 3

        # Check merged buckets
        status_buckets = {
            bucket["key"]: bucket["doc_count"] for bucket in result["status"]["buckets"]
        }
        assert status_buckets["success"] == 18  # 10 + 8
        assert status_buckets["failure"] == 5
        assert status_buckets["pending"] == 3

        # Check new aggregation
        assert "platform" in result
        assert result["platform"]["buckets"][0]["key"] == "aws"

    @patch("app.services.search.AsyncOpenSearch")
    async def test_close(self, mock_es, mock_config_full):
        """Test close method"""

        mock_es_instance = AsyncMock()
        mock_es.return_value = mock_es_instance

        service = ElasticService("elasticsearch")
        service.prev_es = mock_es_instance

        await service.close()

        # Should be called twice - once for new_es and once for prev_es
        assert mock_es_instance.close.call_count == 2


class TestIndexTimestamp:
    """Test class for IndexTimestamp"""

    def test_init(self):
        """Test IndexTimestamp initialization"""
        timestamps = (datetime(2024, 1, 1), datetime(2024, 1, 31))
        index_ts = IndexTimestamp("test-index", timestamps)

        assert index_ts.index == "test-index"
        assert index_ts.timestamps == timestamps

    def test_lt_comparison(self):
        """Test IndexTimestamp less than comparison"""
        ts1 = IndexTimestamp("index1", (datetime(2024, 1, 1), datetime(2024, 1, 31)))
        ts2 = IndexTimestamp("index2", (datetime(2024, 2, 1), datetime(2024, 2, 28)))

        assert ts1 < ts2
        assert not ts2 < ts1


class TestSortedIndexList:
    """Test class for SortedIndexList"""

    def test_insert_and_sort(self):
        """Test insert method maintains sorted order"""
        index_list = SortedIndexList()

        # Insert in non-chronological order
        index_list.insert(
            IndexTimestamp("index2", (datetime(2024, 2, 1), datetime(2024, 2, 28)))
        )
        index_list.insert(
            IndexTimestamp("index1", (datetime(2024, 1, 1), datetime(2024, 1, 31)))
        )
        index_list.insert(
            IndexTimestamp("index3", (datetime(2024, 3, 1), datetime(2024, 3, 31)))
        )

        # Verify sorted order
        assert len(index_list.indices) == 3
        assert index_list.indices[0].index == "index1"
        assert index_list.indices[1].index == "index2"
        assert index_list.indices[2].index == "index3"

    def test_get_indices_in_given_range(self):
        """Test get_indices_in_given_range method"""
        index_list = SortedIndexList()

        # Add test indices
        index_list.insert(
            IndexTimestamp("index1", (datetime(2024, 1, 1), datetime(2024, 1, 31)))
        )
        index_list.insert(
            IndexTimestamp("index2", (datetime(2024, 2, 1), datetime(2024, 2, 28)))
        )
        index_list.insert(
            IndexTimestamp("index3", (datetime(2024, 3, 1), datetime(2024, 3, 31)))
        )

        # Test range query
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 2, 15)

        result = index_list.get_indices_in_given_range(start_date, end_date)

        # Should include indices that overlap with the range
        assert len(result) >= 1


class TestStandaloneFunctions:
    """Test class for standalone functions"""

    def test_flatten_dict_simple(self):
        """Test flatten_dict with simple nested dict"""
        test_dict = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}

        result = flatten_dict(test_dict)

        assert result["a"] == 1
        assert result["b.c"] == 2
        assert result["b.d.e"] == 3

    def test_flatten_dict_with_list(self):
        """Test flatten_dict with list values"""
        test_dict = {"a": [1, 2, {"b": 3}], "c": {"d": [4, 5]}}

        result = flatten_dict(test_dict)

        assert result["a.0"] == 1
        assert result["a.1"] == 2
        assert result["a.2.b"] == 3
        assert result["c.d.0"] == 4
        assert result["c.d.1"] == 5

    def test_removeKeys(self):
        """Test removeKeys function"""
        test_dict = {
            "keep1": "value1",
            "remove1": "value2",
            "keep2": "value3",
            "remove2": "value4",
        }
        keys_to_remove = ["remove1", "remove2"]

        result = removeKeys(test_dict, keys_to_remove)

        assert "keep1" in result
        assert "keep2" in result
        assert "remove1" not in result
        assert "remove2" not in result
        assert result["keep1"] == "value1"
        assert result["keep2"] == "value3"

    def test_buildPlatformFilter(self):
        """Test buildPlatformFilter function"""
        # Test with ROSA-HCP
        upstream_list = ["test-rosa-hcp-job", "other-job"]
        cluster_type_list = ["regular"]

        result = buildPlatformFilter(upstream_list, cluster_type_list)
        assert "AWS ROSA-HCP" in result

        # Test with ROSA cluster type
        upstream_list = ["regular-job"]
        cluster_type_list = ["rosa-cluster", "regular"]

        result = buildPlatformFilter(upstream_list, cluster_type_list)
        assert "AWS ROSA" in result

        # Test with both
        upstream_list = ["test-rosa-hcp-job"]
        cluster_type_list = ["rosa-cluster"]

        result = buildPlatformFilter(upstream_list, cluster_type_list)
        assert "AWS ROSA-HCP" in result
        assert "AWS ROSA" in result

    def test_getBuildFilter(self):
        """Test getBuildFilter function"""
        input_list = [
            "test-job-build-name-4.14.1-rc.1",
            "another-job-long-name-4.15.0-rc.2",
            "short-4.13.5-ga.0",
        ]

        result = getBuildFilter(input_list)

        assert "build-name-4.14.1-rc.1" in result
        assert "long-name-4.15.0-rc.2" in result
        assert "short-4.13.5-ga.0" in result
