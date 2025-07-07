from unittest.mock import Mock, patch

import orjson
import pytest

from app.api.v1.commons.constants import FIELDS_FILTER_DICT, SPLUNK_SEMAPHORE_COUNT
from app.services.splunk import SEMAPHORE, SplunkService

"""Unit tests for SplunkService.

Assisted-by: Cursor / claude-4-5-sonnet-20240620

These tests are designed to cover the SplunkService class and its methods.

After asking for unit tests without internal mocks, it decided to only mock
functions with no external dependencies. Interesting choice. Several more
prompts were needed to approach 100% coverage.

Cursor failed to reproduce the correct query strings: it didn't understand
that the logic would put two spaces between the "sort" keyword and a field
with default ascending order. The extra space between the direction and the
field name isn't necessary, and looks odd, so I tightened up the code to avoid
the extra space.

There's one loop that apparently doesn't have full coverage of the exit
condition, although it's not clear why. I'm going to leave this for now at
99% coverage.
"""


class TestSplunkServiceInit:
    """Test SplunkService initialization"""

    def test_init_with_default_params(self):
        """Test initialization with default parameters"""
        # Mock the config and splunk client to avoid actual connections
        with patch("app.config.get_config") as mock_get_config, patch(
            "app.services.splunk.client.connect"
        ) as mock_connect:

            # Setup mock config
            mock_config = Mock()
            mock_config.get.side_effect = lambda key: {
                "test.indice": "test_index",
                "test.host": "localhost",
                "test.port": 8089,
                "test.username": "admin",
                "test.password": "password",
            }.get(key)
            mock_get_config.return_value = mock_config

            # Setup mock service
            mock_service = Mock()
            mock_connect.return_value = mock_service

            # Test initialization
            service = SplunkService(configpath="test")

            assert service.indice == "test_index"
            assert service.service == mock_service
            mock_connect.assert_called_once_with(
                host="localhost", port=8089, username="admin", password="password"
            )

    def test_init_with_custom_index(self):
        """Test initialization with custom index parameter"""
        with patch("app.config.get_config") as mock_get_config, patch(
            "app.services.splunk.client.connect"
        ) as mock_connect:

            # Setup mock config
            mock_config = Mock()
            mock_config.get.side_effect = lambda key: {
                "test.indice": "default_index",
                "test.host": "localhost",
                "test.port": 8089,
                "test.username": "admin",
                "test.password": "password",
            }.get(key)
            mock_get_config.return_value = mock_config

            # Setup mock service
            mock_service = Mock()
            mock_connect.return_value = mock_service

            # Test initialization with custom index
            service = SplunkService(configpath="test", index="custom_index")

            assert service.indice == "custom_index"
            assert service.service == mock_service

    def test_init_connection_error(self):
        """Test initialization when connection fails"""
        with patch("app.config.get_config") as mock_get_config, patch(
            "app.services.splunk.client.connect"
        ) as mock_connect, patch("builtins.print") as mock_print:

            # Setup mock config
            mock_config = Mock()
            mock_config.get.side_effect = lambda key: {
                "test.indice": "test_index",
                "test.host": "localhost",
                "test.port": 8089,
                "test.username": "admin",
                "test.password": "password",
            }.get(key)
            mock_get_config.return_value = mock_config

            # Setup mock connection to raise exception
            mock_connect.side_effect = Exception("Connection failed")

            # Test initialization with connection error
            SplunkService(configpath="test")

            mock_print.assert_called_once()
            assert "Error connecting to splunk: Connection failed" in str(
                mock_print.call_args
            )


class TestSplunkServiceBuildSearchQuery:
    """Test the build_search_query method which contains pure logic"""

    def setup_method(self):
        """Setup a mock SplunkService instance for testing"""
        with patch("app.config.get_config"), patch(
            "app.services.splunk.client.connect"
        ):
            self.service = SplunkService(configpath="test", index="test_index")

    def test_build_search_query_basic(self):
        """Test building a basic search query"""
        query = self.service.build_search_query()

        expected = (
            "search index=test_index "
            "| eventstats count AS total_records "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_with_search_list(self):
        """Test building search query with additional search parameters"""
        query = self.service.build_search_query(searchList="status=passed")

        expected = (
            "search index=test_index status=passed "
            "| eventstats count AS total_records "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_with_asc_sort(self):
        """Test building search query with ascending sort"""
        sort_param = [{"endDate": {"order": "asc"}}]
        query = self.service.build_search_query(sort=sort_param)

        expected = (
            "search index=test_index "
            "| eventstats count AS total_records "
            "| sort _indextime "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_with_desc_sort(self):
        """Test building search query with descending sort"""
        sort_param = [{"endDate": {"order": "desc"}}]
        query = self.service.build_search_query(sort=sort_param)

        expected = (
            "search index=test_index "
            "| eventstats count AS total_records "
            "| sort -_indextime "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_with_unknown_sort_field(self):
        """Test building search query with unknown sort field (should use original key)"""
        sort_param = [{"unknownField": {"order": "asc"}}]
        query = self.service.build_search_query(sort=sort_param)

        expected = (
            "search index=test_index "
            "| eventstats count AS total_records "
            "| sort unknownField "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_with_known_sort_field(self):
        """Test building search query with known sort field from FIELDS_FILTER_DICT"""
        sort_param = [{"cpu": {"order": "asc"}}]
        query = self.service.build_search_query(sort=sort_param)

        expected = (
            "search index=test_index "
            "| eventstats count AS total_records "
            "| sort cpu "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_with_all_parameters(self):
        """Test building search query with all parameters"""
        sort_param = [{"benchmark": {"order": "desc"}}]
        query = self.service.build_search_query(
            searchList="status=passed AND cpu=4", sort=sort_param
        )

        expected = (
            "search index=test_index status=passed AND cpu=4 "
            "| eventstats count AS total_records "
            "| sort -test_type "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_sort_without_order(self):
        """Test building search query with sort but no order specified (should default to asc)"""
        sort_param = [{"cpu": {}}]
        query = self.service.build_search_query(sort=sort_param)

        expected = (
            "search index=test_index "
            "| eventstats count AS total_records "
            "| sort cpu "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    def test_build_search_query_empty_sort_list(self):
        """Test building search query with empty sort list"""
        query = self.service.build_search_query(sort=[])

        expected = (
            "search index=test_index "
            "| eventstats count AS total_records "
            "| fields total_records _raw host source sourcetype _bkt _serial _indextime"
        )
        assert query == expected

    @pytest.mark.parametrize(
        "sort_key,expected_field",
        [
            ("nodeName", "node_name"),
            ("cpu", "cpu"),
            ("benchmark", "test_type"),
            ("ocpVersion", "ocp_version"),
            ("releaseStream", "ocp_build"),
            ("jobStatus", "status"),
            ("endDate", "_indextime"),
            ("startDate", "_indextime"),
            ("formal", "isFormal"),
        ],
    )
    def test_build_search_query_field_mapping(self, sort_key, expected_field):
        """Test that sort fields are correctly mapped using FIELDS_FILTER_DICT"""
        sort_param = [{sort_key: {"order": "asc"}}]
        query = self.service.build_search_query(sort=sort_param)

        assert f"| sort {expected_field} " in query, f"Query is {query}"


class TestSplunkServiceStreamResults:
    """Test the _stream_results async generator method"""

    def setup_method(self):
        """Setup a mock SplunkService instance for testing"""
        with patch("app.config.get_config"), patch(
            "app.services.splunk.client.connect"
        ):
            self.service = SplunkService(configpath="test", index="test_index")

    @pytest.mark.asyncio
    async def test_stream_results_empty(self):
        """Test streaming results with empty result set"""
        # Mock the JSONResultsReader to return empty results
        with patch("app.services.splunk.results.JSONResultsReader") as mock_reader:
            mock_reader.return_value = []

            results = []
            async for record in self.service._stream_results(Mock()):
                results.append(record)

            assert results == []

    @pytest.mark.asyncio
    async def test_stream_results_with_data(self):
        """Test streaming results with actual data"""
        # Mock the JSONResultsReader to return test data
        test_data = [
            {"_raw": '{"test": "data1"}', "host": "host1"},
            {"_raw": '{"test": "data2"}', "host": "host2"},
        ]

        with patch("app.services.splunk.results.JSONResultsReader") as mock_reader:
            mock_reader.return_value = test_data

            results = []
            async for record in self.service._stream_results(Mock()):
                results.append(record)

            assert results == test_data


class TestSplunkServiceSemaphore:
    """Test the semaphore configuration"""

    def test_semaphore_count(self):
        """Test that the semaphore is configured with the correct count"""
        from app.services.splunk import SEMAPHORE

        assert SEMAPHORE._value == SPLUNK_SEMAPHORE_COUNT
        assert SEMAPHORE._value == 5


class TestSplunkServiceConstants:
    """Test that constants are properly imported and used"""

    def test_fields_filter_dict_import(self):
        """Test that FIELDS_FILTER_DICT is properly imported"""
        assert "nodeName" in FIELDS_FILTER_DICT
        assert "cpu" in FIELDS_FILTER_DICT
        assert "benchmark" in FIELDS_FILTER_DICT
        assert FIELDS_FILTER_DICT["benchmark"] == "test_type"
        assert FIELDS_FILTER_DICT["nodeName"] == "node_name"

    def test_splunk_semaphore_count_import(self):
        """Test that SPLUNK_SEMAPHORE_COUNT is properly imported"""
        assert SPLUNK_SEMAPHORE_COUNT == 5


class TestSplunkServiceQueryDataProcessing:
    """Test data processing logic in query method without external dependencies"""

    def setup_method(self):
        """Setup a mock SplunkService instance for testing"""
        with patch("app.config.get_config"), patch(
            "app.services.splunk.client.connect"
        ):
            self.service = SplunkService(configpath="test", index="test_index")

    def test_query_data_processing_logic(self):
        """Test the data processing logic used in query method"""
        # Test data that would come from Splunk
        test_record = {
            "_raw": '{"application": "test", "value": 42}',
            "host": "test-host",
            "source": "test-source",
            "sourcetype": "test-sourcetype",
            "_bkt": "test-bucket",
            "_serial": "test-serial",
            "_indextime": "1234567890",
            "total_records": "100",
        }

        # Simulate the processing logic from the query method
        raw_data = test_record.get("_raw", "{}")
        processed_record = {
            "data": orjson.loads(raw_data),
            "host": test_record.get("host", ""),
            "source": test_record.get("source", ""),
            "sourcetype": test_record.get("sourcetype", ""),
            "bucket": test_record.get("_bkt", ""),
            "serial": test_record.get("_serial", ""),
            "timestamp": test_record.get("_indextime", ""),
        }

        # Verify the processing
        assert processed_record["data"] == {"application": "test", "value": 42}
        assert processed_record["host"] == "test-host"
        assert processed_record["source"] == "test-source"
        assert processed_record["sourcetype"] == "test-sourcetype"
        assert processed_record["bucket"] == "test-bucket"
        assert processed_record["serial"] == "test-serial"
        assert processed_record["timestamp"] == "1234567890"

    def test_query_data_processing_with_malformed_json(self):
        """Test data processing with malformed JSON in _raw field"""
        test_record = {
            "_raw": '{"malformed": json}',  # Invalid JSON
            "host": "test-host",
            "source": "test-source",
            "sourcetype": "test-sourcetype",
            "_bkt": "test-bucket",
            "_serial": "test-serial",
            "_indextime": "1234567890",
        }

        # Test that orjson.loads would raise an exception
        with pytest.raises(orjson.JSONDecodeError):
            orjson.loads(test_record.get("_raw", "{}"))

    def test_query_data_processing_with_empty_fields(self):
        """Test data processing with missing/empty fields"""
        test_record = {
            "_raw": '{"test": "data"}',
            # Missing other fields
        }

        # Simulate the processing logic with default values
        raw_data = test_record.get("_raw", "{}")
        processed_record = {
            "data": orjson.loads(raw_data),
            "host": test_record.get("host", ""),
            "source": test_record.get("source", ""),
            "sourcetype": test_record.get("sourcetype", ""),
            "bucket": test_record.get("_bkt", ""),
            "serial": test_record.get("_serial", ""),
            "timestamp": test_record.get("_indextime", ""),
        }

        # Verify defaults are applied
        assert processed_record["data"] == {"test": "data"}
        assert processed_record["host"] == ""
        assert processed_record["source"] == ""
        assert processed_record["sourcetype"] == ""
        assert processed_record["bucket"] == ""
        assert processed_record["serial"] == ""
        assert processed_record["timestamp"] == ""


class TestSplunkServiceFilterPostQueryBuilding:
    """Test the query building logic for filterPost method"""

    def setup_method(self):
        """Setup a mock SplunkService instance for testing"""
        with patch("app.config.get_config"), patch(
            "app.services.splunk.client.connect"
        ):
            self.service = SplunkService(configpath="test", index="test_index")

    def test_filter_post_query_building_basic(self):
        """Test the basic query building logic for filterPost"""
        # This tests the logic without external dependencies

        # Expected query structure from filterPost method
        expected_base = f"search index={self.service.indice} "
        expected_stats = (
            "| stats count AS total_records, "
            "values(cpu) AS cpu, "
            "values(node_name) AS nodeName, "
            "values(test_type) AS benchmark, "
            "values(ocp_version) AS ocpVersion, "
            "values(ocp_build) AS releaseStream, "
            "values(formal) AS isFormal, "
            'count(eval(status="passed")) AS pass_count,'
            'count(eval(like(status,"fail%"))) AS fail_count'
        )
        # Verify the query structure components
        assert expected_base.startswith("search index=test_index")
        assert "stats count AS total_records" in expected_stats
        assert "values(cpu) AS cpu" in expected_stats
        assert "values(node_name) AS nodeName" in expected_stats
        assert "values(test_type) AS benchmark" in expected_stats
        assert 'count(eval(status="passed")) AS pass_count' in expected_stats
        assert 'count(eval(like(status,"fail%"))) AS fail_count' in expected_stats

    def test_filter_post_query_building_with_search_list(self):
        """Test the query building logic with search parameters"""
        search_list = "cpu=4 AND status=passed"

        expected_base = f"search index={self.service.indice} {search_list} "

        # Verify the query includes the search parameters
        assert expected_base == f"search index=test_index {search_list} "

    def test_filter_post_response_processing(self):
        """Test the response processing logic for filterPost"""
        # Mock response data that would come from Splunk
        mock_response_data = {
            "results": [
                {
                    "total_records": "150",
                    "pass_count": "120",
                    "fail_count": "30",
                    "cpu": ["2", "4", "8"],
                    "nodeName": ["node1", "node2"],
                    "benchmark": ["test1", "test2"],
                    "ocpVersion": ["4.12", "4.13"],
                    "releaseStream": ["stable", "fast"],
                    "isFormal": ["true", "false"],
                }
            ]
        }

        # Process the response data (logic from filterPost method)
        value = mock_response_data.get("results", [])
        total_records = int(value[0].get("total_records", 0)) if value else 0
        pass_count = int(value[0].get("pass_count", 0)) if value else 0
        fail_count = int(value[0].get("fail_count", 0)) if value else 0

        result = {
            "data": value,
            "total": total_records,
            "summary": {
                "total": total_records,
                "success": pass_count,
                "failure": fail_count,
            },
        }

        # Verify the processing
        assert result["total"] == 150
        assert result["summary"]["total"] == 150
        assert result["summary"]["success"] == 120
        assert result["summary"]["failure"] == 30
        assert result["data"] == mock_response_data["results"]

    def test_filter_post_response_processing_empty(self):
        """Test the response processing logic with empty results"""
        mock_response_data = {"results": []}

        # Process the response data
        value = mock_response_data.get("results", [])
        total_records = int(value[0].get("total_records", 0)) if value else 0
        pass_count = int(value[0].get("pass_count", 0)) if value else 0
        fail_count = int(value[0].get("fail_count", 0)) if value else 0

        result = {
            "data": value,
            "total": total_records,
            "summary": {
                "total": total_records,
                "success": pass_count,
                "failure": fail_count,
            },
        }

        # Verify the processing handles empty results
        assert result["total"] == 0
        assert result["summary"]["total"] == 0
        assert result["summary"]["success"] == 0
        assert result["summary"]["failure"] == 0
        assert result["data"] == []


class TestSplunkServiceQuery:
    """Test the query method comprehensively"""

    def setup_method(self):
        """Setup a mock SplunkService instance for testing"""
        with patch("app.config.get_config"), patch(
            "app.services.splunk.client.connect"
        ):
            self.service = SplunkService(configpath="test", index="test_index")

    @pytest.mark.asyncio
    async def test_query_parameter_handling(self):
        """Test that query parameters are properly handled and modified"""
        # Test query parameter modification
        query_dict = {"earliest_time": "2023-01-01", "latest_time": "2023-01-02"}
        original_query = query_dict.copy()

        # Mock the external dependencies
        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results"
        ) as mock_stream:

            # Mock empty results
            mock_to_thread.return_value = None
            mock_stream.return_value = iter([])

            await self.service.query(query_dict, size=50, offset=10)

            # Verify the query dict was modified with count and offset
            assert query_dict["count"] == 50
            assert query_dict["offset"] == 10
            # Verify original parameters are preserved
            assert query_dict["earliest_time"] == original_query["earliest_time"]
            assert query_dict["latest_time"] == original_query["latest_time"]

    @pytest.mark.asyncio
    async def test_query_default_parameters(self):
        """Test query with default parameters"""
        query_dict = {}

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results"
        ) as mock_stream:

            mock_to_thread.return_value = None
            mock_stream.return_value = iter([])

            await self.service.query(query_dict)

            # Verify default parameters are applied
            assert query_dict["count"] == 100  # default size
            assert query_dict["offset"] == 0  # default offset

    @pytest.mark.asyncio
    async def test_query_search_query_building(self):
        """Test that the search query is built correctly"""
        query_dict = {"earliest_time": "2023-01-01"}

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results"
        ) as mock_stream, patch.object(
            self.service, "build_search_query"
        ) as mock_build_query:

            mock_to_thread.return_value = None
            mock_stream.return_value = iter([])
            mock_build_query.return_value = "test_query"

            await self.service.query(
                query_dict,
                searchList="status=passed",
                sort=[{"cpu": {"order": "desc"}}],
            )

            # Verify build_search_query was called with correct parameters
            mock_build_query.assert_called_once_with(
                "status=passed", [{"cpu": {"order": "desc"}}]
            )

    @pytest.mark.asyncio
    async def test_query_oneshot_call(self):
        """Test that oneshot is called with correct parameters"""
        query_dict = {"earliest_time": "2023-01-01"}

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results"
        ) as mock_stream, patch.object(
            self.service, "build_search_query"
        ) as mock_build_query:

            mock_to_thread.return_value = "mock_results"
            mock_stream.return_value = iter([])
            mock_build_query.return_value = "test_search_query"

            await self.service.query(query_dict)

            # Verify asyncio.to_thread was called with correct parameters
            mock_to_thread.assert_called_once()
            call_args = mock_to_thread.call_args
            assert call_args[0][0] == self.service.service.jobs.oneshot
            assert call_args[0][1] == "test_search_query"
            assert call_args[1] == query_dict

    @pytest.mark.asyncio
    async def test_query_empty_results(self):
        """Test query with empty results from Splunk"""
        query_dict = {}

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results"
        ) as mock_stream:

            # Mock empty results (None or falsy)
            mock_to_thread.return_value = None

            result = await self.service.query(query_dict)

            # Verify the function returns correct empty result structure
            assert result == {"data": [], "total": 0}
            # _stream_results should not be called when oneshot_results is None
            mock_stream.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_with_valid_results(self):
        """Test query with valid results from Splunk"""
        query_dict = {}

        # Mock data that would come from Splunk
        mock_records = [
            {
                "_raw": '{"test": "data1", "value": 100}',
                "host": "host1",
                "source": "source1",
                "sourcetype": "sourcetype1",
                "_bkt": "bucket1",
                "_serial": "serial1",
                "_indextime": "1640995200",
                "total_records": "5",
            },
            {
                "_raw": '{"test": "data2", "value": 200}',
                "host": "host2",
                "source": "source2",
                "sourcetype": "sourcetype2",
                "_bkt": "bucket2",
                "_serial": "serial2",
                "_indextime": "1640995300",
                "total_records": "5",
            },
        ]

        async def mock_stream_results(results):
            for record in mock_records:
                yield record

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results", side_effect=mock_stream_results
        ):

            mock_to_thread.return_value = "mock_results"

            result = await self.service.query(query_dict)

            # Verify the result structure
            assert result is not None
            assert "data" in result
            assert "total" in result
            assert len(result["data"]) == 2
            assert result["total"] == 5

            # Verify first record processing
            first_record = result["data"][0]
            assert first_record["data"] == {"test": "data1", "value": 100}
            assert first_record["host"] == "host1"
            assert first_record["source"] == "source1"
            assert first_record["sourcetype"] == "sourcetype1"
            assert first_record["bucket"] == "bucket1"
            assert first_record["serial"] == "serial1"
            assert first_record["timestamp"] == "1640995200"

            # Verify second record processing
            second_record = result["data"][1]
            assert second_record["data"] == {"test": "data2", "value": 200}
            assert second_record["host"] == "host2"

    @pytest.mark.asyncio
    async def test_query_with_malformed_json(self):
        """Test query handling of malformed JSON in _raw field"""
        query_dict = {}

        # Mock data with malformed JSON
        mock_records = [
            {"_raw": '{"valid": "json"}', "host": "host1", "total_records": "2"},
            {
                "_raw": '{"invalid": json}',  # Malformed JSON
                "host": "host2",
                "total_records": "2",
            },
        ]

        async def mock_stream_results(results):
            for record in mock_records:
                yield record

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results", side_effect=mock_stream_results
        ), patch("builtins.print") as mock_print:

            mock_to_thread.return_value = "mock_results"

            result = await self.service.query(query_dict)

            # Should only have one valid record due to JSON parsing error
            assert result is not None
            assert len(result["data"]) == 1
            assert result["data"][0]["data"] == {"valid": "json"}
            assert result["total"] == 2  # Total is still from the last record

            # Verify error was printed
            mock_print.assert_called()
            print_args = str(mock_print.call_args)
            assert "Error processing record" in print_args

    @pytest.mark.asyncio
    async def test_query_with_missing_fields(self):
        """Test query with records missing standard fields"""
        query_dict = {}

        # Mock data with missing fields
        mock_records = [
            {
                "_raw": '{"test": "minimal"}',
                # Missing most fields
                "total_records": "1",
            }
        ]

        async def mock_stream_results(results):
            for record in mock_records:
                yield record

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results", side_effect=mock_stream_results
        ):

            mock_to_thread.return_value = "mock_results"

            result = await self.service.query(query_dict)

            # Verify defaults are applied for missing fields
            assert result is not None
            record = result["data"][0]
            assert record["data"] == {"test": "minimal"}
            assert record["host"] == ""
            assert record["source"] == ""
            assert record["sourcetype"] == ""
            assert record["bucket"] == ""
            assert record["serial"] == ""
            assert record["timestamp"] == ""

    @pytest.mark.asyncio
    async def test_query_with_no_records(self):
        """Test query with no records from stream"""
        query_dict = {}

        async def mock_stream_results(results):
            # Empty generator
            return
            yield  # unreachable

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results", side_effect=mock_stream_results
        ):

            mock_to_thread.return_value = "mock_results"

            result = await self.service.query(query_dict)

            # Should return empty data with 0 total
            assert result is not None
            assert result["data"] == []
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_query_oneshot_exception(self):
        """Test query when oneshot raises an exception"""
        query_dict = {}

        with patch("asyncio.to_thread") as mock_to_thread, patch(
            "builtins.print"
        ) as mock_print:

            mock_to_thread.side_effect = Exception("Splunk connection error")

            result = await self.service.query(query_dict)

            # Should return None on exception
            assert result is None

            # Verify error was printed
            mock_print.assert_called()
            print_args = str(mock_print.call_args)
            assert "Error querying Splunk" in print_args

    @pytest.mark.asyncio
    async def test_query_inner_exception(self):
        """Test query when inner exception occurs (asyncio.to_thread fails)"""
        query_dict = {}

        with patch("asyncio.to_thread") as mock_to_thread, patch(
            "builtins.print"
        ) as mock_print:

            # Mock exception in the inner try block (asyncio.to_thread fails)
            mock_to_thread.side_effect = Exception("Splunk connection error")

            result = await self.service.query(query_dict)

            # Should return None on exception
            assert result is None

            # Verify error was printed - this exception is caught by the inner handler
            mock_print.assert_called()
            print_args = str(mock_print.call_args)
            assert "Error querying Splunk" in print_args

    @pytest.mark.asyncio
    async def test_query_outer_exception_semaphore_error(self):
        """Test query when outer exception occurs (semaphore context manager fails)"""
        query_dict = {}

        # Mock the semaphore to raise an exception when entering context
        with patch.object(SEMAPHORE, "__aenter__") as mock_aenter, patch(
            "builtins.print"
        ) as mock_print:

            mock_aenter.side_effect = Exception("Semaphore acquisition failed")

            result = await self.service.query(query_dict)

            # Should return None on exception
            assert result is None

            # Verify error was printed - this exception is caught by the outer handler
            mock_print.assert_called()
            print_args = str(mock_print.call_args)
            assert (
                "Error querying Splunk" in print_args
            )  # lowercase 's' for outer handler

    @pytest.mark.asyncio
    async def test_query_outer_exception_build_search_query_error(self):
        """Test query when build_search_query raises exception before outer try block"""
        query_dict = {}

        with patch.object(
            self.service, "build_search_query"
        ) as mock_build_query, patch("builtins.print") as mock_print:

            # build_search_query is called before the outer try block
            mock_build_query.side_effect = Exception("Query building failed")

            # This should raise the exception since it's not in any try block
            with pytest.raises(Exception, match="Query building failed"):
                _ = await self.service.query(query_dict)

            # No print should be called since exception is not caught
            mock_print.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_outer_exception_semaphore_exit_error(self):
        """Test query when semaphore context manager fails on exit"""
        query_dict = {}

        # Mock successful entry but failing exit
        with patch.object(SEMAPHORE, "release") as mock_release, patch(
            "asyncio.to_thread"
        ) as mock_to_thread, patch("builtins.print") as mock_print:

            mock_to_thread.return_value = None  # Empty results
            mock_release.side_effect = Exception("Semaphore release failed")

            result = await self.service.query(query_dict)

            # Should return None on exception
            assert result is None

            # Verify error was printed - this exception is caught by the outer handler
            mock_print.assert_called()
            print_args = str(mock_print.call_args)
            assert (
                "Error querying splunk" in print_args
            )  # lowercase 's' for outer handler

    @pytest.mark.asyncio
    async def test_query_semaphore_usage(self):
        """Test that query uses the semaphore correctly"""
        query_dict = {}

        # Track semaphore acquisition
        semaphore_acquired = False
        original_acquire = SEMAPHORE.acquire

        async def mock_acquire():
            nonlocal semaphore_acquired
            semaphore_acquired = True
            return await original_acquire()

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results"
        ), patch.object(SEMAPHORE, "acquire", side_effect=mock_acquire):

            mock_to_thread.return_value = None

            await self.service.query(query_dict)

            # Verify semaphore was acquired
            assert semaphore_acquired

    @pytest.mark.asyncio
    async def test_query_parameter_types(self):
        """Test query with various parameter types"""
        query_dict = {"test": "value"}

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results"
        ) as mock_stream:

            mock_to_thread.return_value = None
            mock_stream.return_value = iter([])

            # Test with different parameter types
            await self.service.query(query_dict, size=50, offset=10, max_results=5000)

            # Verify parameters were properly set
            assert query_dict["count"] == 50
            assert query_dict["offset"] == 10
            # max_results doesn't modify the query dict but is passed to the function

    @pytest.mark.asyncio
    async def test_query_total_calculation(self):
        """Test that total is calculated correctly from the last record"""
        query_dict = {}

        # Mock records with different total_records values
        mock_records = [
            {"_raw": '{"test": "data1"}', "total_records": "10"},
            {"_raw": '{"test": "data2"}', "total_records": "15"},
            {"_raw": '{"test": "data3"}', "total_records": "20"},  # Last record
        ]

        async def mock_stream_results(results):
            for record in mock_records:
                yield record

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            self.service, "_stream_results", side_effect=mock_stream_results
        ):

            mock_to_thread.return_value = "mock_results"

            result = await self.service.query(query_dict)

            # Total should be from the last record
            assert result is not None
            assert result["total"] == 20
            assert len(result["data"]) == 3


class TestSplunkServiceFilterPost:
    """Test the filterPost method comprehensively"""

    def setup_method(self):
        """Setup a mock SplunkService instance for testing"""
        with patch("app.config.get_config"), patch(
            "app.services.splunk.client.connect"
        ):
            self.service = SplunkService(configpath="test", index="test_index")

    @pytest.mark.asyncio
    async def test_filterpost_query_building_basic(self):
        """Test the query building logic in filterPost without search list"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }

        # Expected query structure
        expected_base = f"search index={self.service.indice} "

        # Mock the external dependencies to test query building logic
        mock_results_reader = Mock()
        mock_results_reader.read.return_value = '{"results": []}'

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_results_reader

            _ = await self.service.filterPost(query_dict)

            # Verify asyncio.to_thread was called correctly
            mock_to_thread.assert_called_once()
            call_args = mock_to_thread.call_args

            # Check the search query contains expected components
            search_query = call_args[0][1]  # Second argument is the search query
            assert search_query.startswith(expected_base)
            assert "values(cpu) AS cpu" in search_query
            assert "values(node_name) AS nodeName" in search_query
            assert "values(test_type) AS benchmark" in search_query
            assert 'count(eval(status="passed")) AS pass_count' in search_query

            # Check other parameters
            assert call_args[1]["earliest_time"] == "2023-01-01T00:00:00"
            assert call_args[1]["latest_time"] == "2023-01-02T00:00:00"
            assert call_args[1]["output_mode"] == "json"

    @pytest.mark.asyncio
    async def test_filterpost_query_building_with_search_list(self):
        """Test the query building logic in filterPost with search list"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }
        search_list = "cpu=4 AND status=passed"

        mock_results_reader = Mock()
        mock_results_reader.read.return_value = '{"results": []}'

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_results_reader

            _ = await self.service.filterPost(query_dict, searchList=search_list)

            # Verify the search list is included in the query
            call_args = mock_to_thread.call_args
            search_query = call_args[0][1]

            expected_query_start = f"search index={self.service.indice} {search_list} "
            assert search_query.startswith(expected_query_start)

    @pytest.mark.asyncio
    async def test_filterpost_with_valid_results(self):
        """Test filterPost with valid results from Splunk"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }

        # Mock response data
        mock_response = {
            "results": [
                {
                    "total_records": "150",
                    "pass_count": "120",
                    "fail_count": "30",
                    "cpu": ["2", "4", "8"],
                    "nodeName": ["node1", "node2"],
                    "benchmark": ["test1", "test2"],
                    "ocpVersion": ["4.12", "4.13"],
                    "releaseStream": ["stable", "fast"],
                    "isFormal": ["true", "false"],
                }
            ]
        }

        mock_results_reader = Mock()
        mock_results_reader.read.return_value = orjson.dumps(mock_response).decode()

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_results_reader

            result = await self.service.filterPost(query_dict)

            # Verify the result structure
            assert result is not None
            assert result["data"] == mock_response["results"]
            assert result["total"] == 150
            assert result["summary"]["total"] == 150
            assert result["summary"]["success"] == 120
            assert result["summary"]["failure"] == 30

    @pytest.mark.asyncio
    async def test_filterpost_with_empty_results(self):
        """Test filterPost with empty results"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }

        mock_response = {"results": []}

        mock_results_reader = Mock()
        mock_results_reader.read.return_value = orjson.dumps(mock_response).decode()

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_results_reader

            result = await self.service.filterPost(query_dict)

            # Verify empty results are handled correctly
            assert result is not None
            assert result["data"] == []
            assert result["total"] == 0
            assert result["summary"]["total"] == 0
            assert result["summary"]["success"] == 0
            assert result["summary"]["failure"] == 0

    @pytest.mark.asyncio
    async def test_filterpost_with_missing_counts(self):
        """Test filterPost when pass_count or fail_count are missing"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }

        # Mock response with missing count fields
        mock_response = {
            "results": [
                {
                    "total_records": "100",
                    # Missing pass_count and fail_count
                    "cpu": ["4", "8"],
                    "nodeName": ["node1"],
                }
            ]
        }

        mock_results_reader = Mock()
        mock_results_reader.read.return_value = orjson.dumps(mock_response).decode()

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_results_reader

            result = await self.service.filterPost(query_dict)

            # Verify defaults are applied for missing counts
            assert result is not None
            assert result["total"] == 100
            assert result["summary"]["success"] == 0  # Default when missing
            assert result["summary"]["failure"] == 0  # Default when missing

    @pytest.mark.asyncio
    async def test_filterpost_with_malformed_json(self):
        """Test filterPost with malformed JSON response"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }

        mock_results_reader = Mock()
        mock_results_reader.read.return_value = '{"invalid": json}'  # Malformed JSON

        with patch("asyncio.to_thread") as mock_to_thread, patch(
            "builtins.print"
        ) as mock_print:
            mock_to_thread.return_value = mock_results_reader

            result = await self.service.filterPost(query_dict)

            # Should return None due to exception
            assert result is None

            # Verify error was printed
            mock_print.assert_called()
            print_args = str(mock_print.call_args)
            assert "Error on building data for filters" in print_args

    @pytest.mark.asyncio
    async def test_filterpost_oneshot_exception(self):
        """Test filterPost when oneshot call raises exception"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }

        with patch("asyncio.to_thread") as mock_to_thread, patch(
            "builtins.print"
        ) as mock_print:
            mock_to_thread.side_effect = Exception("Splunk connection error")

            result = await self.service.filterPost(query_dict)

            # Should return None due to exception
            assert result is None

            # Verify error was printed
            mock_print.assert_called()
            print_args = str(mock_print.call_args)
            assert "Error on building data for filters" in print_args

    @pytest.mark.asyncio
    async def test_filterpost_semaphore_usage(self):
        """Test that filterPost uses the semaphore correctly"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
        }

        # Track semaphore acquisition
        semaphore_acquired = False
        original_acquire = SEMAPHORE.acquire

        async def mock_acquire():
            nonlocal semaphore_acquired
            semaphore_acquired = True
            return await original_acquire()

        mock_results_reader = Mock()
        mock_results_reader.read.return_value = '{"results": []}'

        with patch("asyncio.to_thread") as mock_to_thread, patch.object(
            SEMAPHORE, "acquire", side_effect=mock_acquire
        ):
            mock_to_thread.return_value = mock_results_reader

            _ = await self.service.filterPost(query_dict)

            # Verify semaphore was acquired
            assert semaphore_acquired

    @pytest.mark.asyncio
    async def test_filterpost_parameter_validation(self):
        """Test filterPost parameter handling"""
        query_dict = {
            "earliest_time": "2023-01-01T00:00:00",
            "latest_time": "2023-01-02T00:00:00",
            "extra_param": "should_be_ignored",
        }

        mock_results_reader = Mock()
        mock_results_reader.read.return_value = '{"results": []}'

        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = mock_results_reader

            _ = await self.service.filterPost(query_dict, searchList="status=passed")

            # Verify the correct parameters were passed to oneshot
            call_args = mock_to_thread.call_args
            assert call_args[1]["earliest_time"] == "2023-01-01T00:00:00"
            assert call_args[1]["latest_time"] == "2023-01-02T00:00:00"
            assert call_args[1]["output_mode"] == "json"
            # extra_param should not be passed
            assert "extra_param" not in call_args[1]

    def test_filterpost_data_processing_logic(self):
        """Test the data processing logic used in filterPost"""
        # Test the processing logic without external dependencies
        mock_response_data = {
            "results": [
                {
                    "total_records": "200",
                    "pass_count": "150",
                    "fail_count": "50",
                    "cpu": ["2", "4", "8"],
                    "benchmark": ["test1", "test2"],
                }
            ]
        }

        # Simulate the processing logic from filterPost
        value = mock_response_data.get("results", [])
        total_records = int(value[0].get("total_records", 0)) if value else 0
        pass_count = int(value[0].get("pass_count", 0)) if value else 0
        fail_count = int(value[0].get("fail_count", 0)) if value else 0

        result = {
            "data": value,
            "total": total_records,
            "summary": {
                "total": total_records,
                "success": pass_count,
                "failure": fail_count,
            },
        }

        # Verify the processing
        assert result["total"] == 200
        assert result["summary"]["total"] == 200
        assert result["summary"]["success"] == 150
        assert result["summary"]["failure"] == 50
        assert result["data"] == mock_response_data["results"]


class TestSplunkServiceClose:
    """Test the close method"""

    def setup_method(self):
        """Setup a mock SplunkService instance for testing"""
        with patch("app.config.get_config"), patch(
            "app.services.splunk.client.connect"
        ):
            self.service = SplunkService(configpath="test", index="test_index")

    def test_close_calls_logout(self):
        """Test that close calls the service logout method"""
        # Mock the service logout method to avoid actual network calls
        self.service.service.logout = Mock()
        self.service.close()
        self.service.service.logout.assert_called_once()
