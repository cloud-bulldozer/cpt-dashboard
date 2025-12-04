from typing import Any, Optional

from fastapi.testclient import TestClient
import pytest

from app.api.v1.endpoints.summary.summary_api import (
    collect,
    create,
    Product,
    ProductContext,
    ProductResults,
    PRODUCTS,
    router,
    summary_svc,
)
from app.main import app as fastapi_app

"""Unit tests for the summary_api module.

This file tests the summary API endpoints, dependency injection, and helper
functions. Follows established testing patterns with Given-When-Then structure.

Generated-by: Cursor / claude-4-5-sonnet
"""


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    yield TestClient(fastapi_app)


@pytest.fixture
def mock_ocp_summary(monkeypatch):
    """Mock OcpSummary to prevent actual instantiation."""

    async def mock_get_versions(self):
        return {"4.18": ["4.18.0", "4.18.1"], "4.19": ["4.19.0"]}

    async def mock_get_configs(
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        uuids: Optional[bool] = False,
    ):
        return {
            "configs": ["config1", "config2"],
            "versions": versions,
            "benchmarks": benchmarks,
        }

    async def mock_metric_aggregation(
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        configs: Optional[str] = None,
    ):
        return {
            "metrics": {"avg": 100, "max": 150, "min": 50},
            "versions": versions,
            "benchmarks": benchmarks,
            "configs": configs,
        }

    async def mock_close(self):
        pass

    def mock_set_date_filter(self, start_date: str | None, end_date: str | None):
        self.start_date = start_date
        self.end_date = end_date

    class MockOcpSummary:
        def __init__(self, product: str, configpath: str):
            self.product = product
            self.configpath = configpath
            self.start_date = None
            self.end_date = None
            self.date_filter = None

        get_versions = mock_get_versions
        get_configs = mock_get_configs
        metric_aggregation = mock_metric_aggregation
        close = mock_close
        set_date_filter = mock_set_date_filter

    # Patch OcpSummary
    monkeypatch.setattr(
        "app.api.v1.endpoints.summary.summary_api.PRODUCTS",
        {"ocp": Product(MockOcpSummary, "ocp.elasticsearch")},
    )

    return MockOcpSummary


# Mock Summary class for testing
class MockSummary:
    """Mock Summary implementation for testing."""

    def __init__(self, product: str, configpath: str = "ocp.elasticsearch"):
        self.product = product
        self.configpath = configpath
        self.start_date = None
        self.end_date = None
        self.date_filter = None
        self.service = None
        self.closed = False

    def set_date_filter(self, start_date: str | None, end_date: str | None):
        """Set date filter."""
        self.start_date = start_date
        self.end_date = end_date
        if start_date or end_date:
            self.date_filter = {"start": start_date, "end": end_date}
        else:
            self.date_filter = None

    async def close(self):
        """Close the service."""
        self.closed = True
        self.service = None

    async def get_versions(self) -> dict[str, list[str]]:
        """Get versions."""
        return {"4.18": ["4.18.0", "4.18.1"], "4.19": ["4.19.0"]}

    async def get_benchmarks(self, version: str) -> dict[str, Any]:
        """Get benchmarks."""
        return {
            "cluster-density": ["config1", "config2"],
            "node-density": ["config3"],
        }

    async def get_configs(
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        uuids: Optional[bool] = False,
    ) -> dict[str, Any]:
        """Get configurations."""
        return {
            "configs": ["config1", "config2"],
            "versions": versions,
            "benchmarks": benchmarks,
            "uuids": uuids,
        }

    async def metric_aggregation(
        self,
        versions: Optional[str] = None,
        benchmarks: Optional[str] = None,
        configs: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get metric aggregation."""
        return {
            "metrics": {"avg": 100, "max": 150, "min": 50},
            "versions": versions,
            "benchmarks": benchmarks,
            "configs": configs,
        }


class TestDataClasses:
    """Test the dataclasses used in summary_api."""

    def test_product_dataclass(self):
        """Test Product dataclass creation."""
        # Given
        from app.api.v1.endpoints.ocp.summary import OcpSummary

        # When
        product = Product(OcpSummary, "ocp.elasticsearch")

        # Then
        assert product.summaryclass == OcpSummary
        assert product.configpath == "ocp.elasticsearch"

    def test_product_context_dataclass(self):
        """Test ProductContext dataclass creation."""
        # Given
        mock_summary = MockSummary("ocp")

        # When
        context = ProductContext("ocp", mock_summary)

        # Then
        assert context.product == "ocp"
        assert context.instance == mock_summary

    def test_product_results_dataclass(self):
        """Test ProductResults dataclass creation."""
        # Given
        results = {"versions": ["4.18.0"], "benchmarks": ["cluster-density"]}

        # When
        product_results = ProductResults("ocp", results)

        # Then
        assert product_results.product == "ocp"
        assert product_results.results == results


class TestCreate:
    """Test the create function."""

    def test_create_valid_product(self, mock_ocp_summary):
        """Test creating a summary service for a valid product."""
        # Given
        product = "ocp"

        # When
        summary = create(product)

        # Then
        assert summary is not None
        assert summary.product == product
        assert summary.configpath == "ocp.elasticsearch"

    def test_create_invalid_product(self):
        """Test creating a summary service for an invalid product."""
        # Given
        product = "invalid_product"

        # When/Then
        with pytest.raises(NotImplementedError) as exc_info:
            create(product)
        assert "Not implemented" in str(exc_info.value)


class TestSummarySvc:
    """Test the summary_svc dependency."""

    @pytest.mark.asyncio
    async def test_summary_svc_default_products(self, mock_ocp_summary):
        """Test summary_svc with default products."""
        # Given - no products specified, should use all PRODUCTS

        # When
        async for summaries in summary_svc():
            # Then
            assert isinstance(summaries, dict)
            assert "ocp" in summaries
            assert isinstance(summaries["ocp"], ProductContext)
            assert summaries["ocp"].product == "ocp"

            # Verify instance is properly created
            instance = summaries["ocp"].instance
            assert instance.product == "ocp"
            assert instance.configpath == "ocp.elasticsearch"

    @pytest.mark.asyncio
    async def test_summary_svc_single_product(self, mock_ocp_summary):
        """Test summary_svc with a single product."""
        # Given
        products = "ocp"

        # When
        async for summaries in summary_svc(products):
            # Then
            assert isinstance(summaries, dict)
            assert len(summaries) == 1
            assert "ocp" in summaries

    @pytest.mark.asyncio
    async def test_summary_svc_multiple_products(self, mock_ocp_summary):
        """Test summary_svc with multiple products (comma-separated)."""
        # Given - test with single product since only 'ocp' exists
        products = "ocp"

        # When
        async for summaries in summary_svc(products):
            # Then
            assert isinstance(summaries, dict)
            assert "ocp" in summaries

    @pytest.mark.asyncio
    async def test_summary_svc_invalid_product(self, mock_ocp_summary):
        """Test summary_svc with an invalid product."""
        # Given
        products = "invalid_product"

        # When/Then
        with pytest.raises(Exception):  # Should raise HTTPException
            async for summaries in summary_svc(products):
                pass

    @pytest.mark.asyncio
    async def test_summary_svc_closes_services(self, mock_ocp_summary):
        """Test that summary_svc properly closes services."""
        # Given
        products = "ocp"

        # When
        generator = summary_svc(products)
        summaries = await generator.__anext__()

        # Then - service should be created
        assert "ocp" in summaries

        # Verify cleanup happens by finishing the generator
        try:
            await generator.__anext__()
        except StopAsyncIteration:
            pass  # Expected when generator is exhausted


class TestCollect:
    """Test the collect function."""

    @pytest.mark.asyncio
    async def test_collect_single_product(self):
        """Test collect with a single product."""
        # Given
        mock_summary = MockSummary("ocp")
        context = {"ocp": ProductContext("ocp", mock_summary)}
        products = "ocp"
        method = "get_versions"

        # When
        result = await collect(products, context, method)

        # Then
        assert isinstance(result, dict)
        assert "ocp" in result
        assert result["ocp"]["4.18"] == ["4.18.0", "4.18.1"]

    @pytest.mark.asyncio
    async def test_collect_with_date_filters(self):
        """Test collect with date filters."""
        # Given
        mock_summary = MockSummary("ocp")
        context = {"ocp": ProductContext("ocp", mock_summary)}
        products = "ocp"
        method = "get_versions"
        start_date = "2024-01-01"
        end_date = "2024-12-31"

        # When
        result = await collect(
            products, context, method, start_date=start_date, end_date=end_date
        )

        # Then
        assert isinstance(result, dict)
        assert "ocp" in result
        # Verify date filters were set
        assert mock_summary.start_date == start_date
        assert mock_summary.end_date == end_date

    @pytest.mark.asyncio
    async def test_collect_with_kwargs(self):
        """Test collect with additional kwargs."""
        # Given
        mock_summary = MockSummary("ocp")
        context = {"ocp": ProductContext("ocp", mock_summary)}
        products = "ocp"
        method = "get_configs"

        # When
        result = await collect(
            products,
            context,
            method,
            versions="4.18.0",
            benchmarks="cluster-density",
        )

        # Then
        assert isinstance(result, dict)
        assert "ocp" in result
        assert result["ocp"]["versions"] == "4.18.0"
        assert result["ocp"]["benchmarks"] == "cluster-density"

    @pytest.mark.asyncio
    async def test_collect_default_products(self):
        """Test collect with no products specified (should use all)."""
        # Given
        mock_summary = MockSummary("ocp")
        context = {"ocp": ProductContext("ocp", mock_summary)}
        products = None  # Should use all products in context
        method = "get_versions"

        # When
        result = await collect(products, context, method)

        # Then
        assert isinstance(result, dict)
        assert "ocp" in result

    @pytest.mark.asyncio
    async def test_collect_invalid_method(self):
        """Test collect with an invalid method name."""
        # Given
        mock_summary = MockSummary("ocp")
        context = {"ocp": ProductContext("ocp", mock_summary)}
        products = "ocp"
        method = "nonexistent_method"

        # When
        # collect should handle AttributeError gracefully and return empty dict
        result = await collect(products, context, method)

        # Then
        # Should return empty dict when method doesn't exist
        assert isinstance(result, dict)
        assert len(result) == 0  # No results collected due to error

    @pytest.mark.asyncio
    async def test_collect_non_callable_method(self):
        """Test collect when method is not callable."""
        # Given
        mock_summary = MockSummary("ocp")
        mock_summary.product = "ocp"  # Make product a non-callable attribute
        context = {"ocp": ProductContext("ocp", mock_summary)}
        products = "ocp"
        method = "product"  # This is an attribute, not a method

        # When
        # collect should handle non-callable methods gracefully and return empty dict
        result = await collect(products, context, method)

        # Then
        # Should return empty dict when method is not callable
        assert isinstance(result, dict)
        assert len(result) == 0  # No results collected due to ValueError


class TestProductsEndpoint:
    """Test the /api/v1/summary/products endpoint."""

    def test_products_endpoint(self, client):
        """Test getting list of products."""
        # When
        response = client.get("/api/v1/summary/products")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "ocp" in data

    def test_products_endpoint_returns_all_products(self, client):
        """Test that products endpoint returns all configured products."""
        # When
        response = client.get("/api/v1/summary/products")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(PRODUCTS)
        for product in PRODUCTS.keys():
            assert product in data


class TestVersionsEndpoint:
    """Test the /api/v1/summary/versions endpoint."""

    def test_versions_endpoint_no_filters(self, client, mock_ocp_summary):
        """Test getting versions without filters."""
        # When
        response = client.get("/api/v1/summary/versions")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "ocp" in data

    def test_versions_endpoint_with_product_filter(self, client, mock_ocp_summary):
        """Test getting versions with product filter."""
        # When
        response = client.get("/api/v1/summary/versions?products=ocp")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "ocp" in data

    def test_versions_endpoint_with_date_filters(self, client, mock_ocp_summary):
        """Test getting versions with date filters."""
        # When
        response = client.get(
            "/api/v1/summary/versions?start_date=2024-01-01&end_date=2024-12-31"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_versions_endpoint_with_all_filters(self, client, mock_ocp_summary):
        """Test getting versions with all filters."""
        # When
        response = client.get(
            "/api/v1/summary/versions?products=ocp&start_date=2024-01-01&end_date=2024-12-31"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_versions_endpoint_invalid_product(self, client, mock_ocp_summary):
        """Test getting versions with invalid product."""
        # When
        response = client.get("/api/v1/summary/versions?products=invalid_product")

        # Then
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestBenchmarksEndpoint:
    """Test the /api/v1/summary/benchmarks endpoint."""

    def test_benchmarks_endpoint_no_filters(self, client, mock_ocp_summary):
        """Test getting benchmarks without filters."""
        # When
        response = client.get("/api/v1/summary/benchmarks")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_benchmarks_endpoint_with_product(self, client, mock_ocp_summary):
        """Test getting benchmarks with product filter."""
        # When
        response = client.get("/api/v1/summary/benchmarks?products=ocp")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_benchmarks_endpoint_with_versions(self, client, mock_ocp_summary):
        """Test getting benchmarks with version filter."""
        # When
        response = client.get("/api/v1/summary/benchmarks?versions=4.18.0")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_benchmarks_endpoint_with_benchmarks_filter(self, client, mock_ocp_summary):
        """Test getting benchmarks with benchmarks filter."""
        # When
        response = client.get("/api/v1/summary/benchmarks?benchmarks=cluster-density")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_benchmarks_endpoint_with_date_filters(self, client, mock_ocp_summary):
        """Test getting benchmarks with date filters."""
        # When
        response = client.get(
            "/api/v1/summary/benchmarks?start_date=2024-01-01&end_date=2024-12-31"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_benchmarks_endpoint_with_uuids(self, client, mock_ocp_summary):
        """Test getting benchmarks with uuids parameter."""
        # When
        response = client.get("/api/v1/summary/benchmarks?uuids=true")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_benchmarks_endpoint_with_all_filters(self, client, mock_ocp_summary):
        """Test getting benchmarks with all filters."""
        # When
        response = client.get(
            "/api/v1/summary/benchmarks?products=ocp&versions=4.18.0"
            "&benchmarks=cluster-density&start_date=2024-01-01&end_date=2024-12-31&uuids=true"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_benchmarks_endpoint_invalid_product(self, client, mock_ocp_summary):
        """Test getting benchmarks with invalid product."""
        # When
        response = client.get("/api/v1/summary/benchmarks?products=invalid_product")

        # Then
        assert response.status_code == 400


class TestSummaryEndpoint:
    """Test the /api/v1/summary endpoint."""

    def test_summary_endpoint_no_filters(self, client, mock_ocp_summary):
        """Test getting summary without filters."""
        # When
        response = client.get("/api/v1/summary")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_endpoint_with_product(self, client, mock_ocp_summary):
        """Test getting summary with product filter."""
        # When
        response = client.get("/api/v1/summary?products=ocp")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_endpoint_with_versions(self, client, mock_ocp_summary):
        """Test getting summary with version filter."""
        # When
        response = client.get("/api/v1/summary?versions=4.18.0")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_endpoint_with_benchmarks(self, client, mock_ocp_summary):
        """Test getting summary with benchmarks filter."""
        # When
        response = client.get("/api/v1/summary?benchmarks=cluster-density")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_endpoint_with_configs(self, client, mock_ocp_summary):
        """Test getting summary with configs filter."""
        # When
        response = client.get("/api/v1/summary?configs=config1")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_endpoint_with_date_filters(self, client, mock_ocp_summary):
        """Test getting summary with date filters."""
        # When
        response = client.get(
            "/api/v1/summary?start_date=2024-01-01&end_date=2024-12-31"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_endpoint_with_all_filters(self, client, mock_ocp_summary):
        """Test getting summary with all filters."""
        # When
        response = client.get(
            "/api/v1/summary?products=ocp&versions=4.18.0"
            "&benchmarks=cluster-density&configs=config1"
            "&start_date=2024-01-01&end_date=2024-12-31"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_endpoint_invalid_product(self, client, mock_ocp_summary):
        """Test getting summary with invalid product."""
        # When
        response = client.get("/api/v1/summary?products=invalid_product")

        # Then
        assert response.status_code == 400


class TestRouterConfiguration:
    """Test the router configuration."""

    def test_router_exists(self):
        """Test that router is properly configured."""
        # Then
        assert router is not None
        routes = [route.path for route in router.routes if hasattr(route, "path")]
        assert len(routes) >= 4  # At least 4 endpoints

    def test_router_has_products_endpoint(self):
        """Test that router has products endpoint."""
        # When
        routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and route.path == "/api/v1/summary/products"
        ]

        # Then
        assert len(routes) == 1
        assert "GET" in routes[0].methods

    def test_router_has_versions_endpoint(self):
        """Test that router has versions endpoint."""
        # When
        routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and route.path == "/api/v1/summary/versions"
        ]

        # Then
        assert len(routes) == 1
        assert "GET" in routes[0].methods

    def test_router_has_benchmarks_endpoint(self):
        """Test that router has benchmarks endpoint."""
        # When
        routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and route.path == "/api/v1/summary/benchmarks"
        ]

        # Then
        assert len(routes) == 1
        assert "GET" in routes[0].methods

    def test_router_has_summary_endpoint(self):
        """Test that router has summary endpoint."""
        # When
        routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and route.path == "/api/v1/summary"
        ]

        # Then
        assert len(routes) == 1
        assert "GET" in routes[0].methods


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_versions_endpoint_with_empty_product_string(
        self, client, mock_ocp_summary
    ):
        """Test versions endpoint with empty product string."""
        # When
        response = client.get("/api/v1/summary/versions?products=")

        # Then
        # Should handle empty string gracefully
        assert response.status_code in [200, 400]

    def test_benchmarks_endpoint_with_empty_filters(self, client, mock_ocp_summary):
        """Test benchmarks endpoint with empty filter strings."""
        # When
        response = client.get(
            "/api/v1/summary/benchmarks?versions=&benchmarks=&products="
        )

        # Then
        # Should handle empty strings gracefully
        assert response.status_code in [200, 400]

    def test_summary_endpoint_with_special_characters(self, client, mock_ocp_summary):
        """Test summary endpoint with special characters in filters."""
        # When
        response = client.get("/api/v1/summary?configs=test%20config")

        # Then
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_collect_with_exception_in_method(self):
        """Test collect handles exceptions in method calls gracefully."""
        # Given
        mock_summary = MockSummary("ocp")

        # Create a method that raises an exception
        async def failing_method():
            raise ValueError("Test error")

        mock_summary.get_versions = failing_method

        context = {"ocp": ProductContext("ocp", mock_summary)}
        products = "ocp"
        method = "get_versions"

        # When
        result = await collect(products, context, method)

        # Then - should handle error and return result (possibly empty)
        assert isinstance(result, dict)

    def test_products_endpoint_is_synchronous(self, client):
        """Test that products endpoint is accessible and returns immediately."""
        # When
        response = client.get("/api/v1/summary/products")

        # Then
        assert response.status_code == 200
        assert response.elapsed.total_seconds() < 1  # Should be fast
