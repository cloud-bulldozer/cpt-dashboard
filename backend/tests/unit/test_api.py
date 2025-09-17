import json
from unittest.mock import mock_open, patch

from fastapi.testclient import TestClient
import pytest

from app.api.api import router, version
from app.main import app as fastapi_app

"""Unit tests for the main API router and version endpoint.

This file tests the main API router configuration and the version endpoint
functionality including various error scenarios.
"""


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    yield TestClient(fastapi_app)


class TestVersionEndpoint:

    @pytest.mark.asyncio
    async def test_version_endpoint_with_valid_file(self):
        """Test version endpoint when version.json exists and contains valid data."""
        # Expected
        expected_version_data = {
            "version": "1.2.3",
            "sha": "abc123def456",
            "branch": "main",
            "display_version": "v1.2.3-abc123def456 (main)",
            "date": "2025-01-15T10:30:00.000000+00:00",
            "changes": [
                {
                    "sha": "abc123",
                    "author": "Test Author",
                    "email": "test@example.com",
                    "date": "2025-01-14T14:52:38-04:00",
                    "title": "Add new feature",
                }
            ],
        }

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True
            mock_file_content = json.dumps(expected_version_data)
            mock_version_file.open.return_value = mock_open(
                read_data=mock_file_content
            ).return_value

            # Match against expected
            result = await version()
            assert isinstance(result, dict)
            assert result == expected_version_data

    @pytest.mark.asyncio
    async def test_version_endpoint_file_not_exists(self):
        """Test version endpoint when version.json doesn't exist."""
        # Expected
        expected_default = {"version": "0.0.0-none", "changes": []}

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = False

            # Match against expected
            result = await version()
            assert isinstance(result, dict)
            assert result == expected_default

    @pytest.mark.asyncio
    async def test_version_endpoint_invalid_json(self):
        """Test version endpoint when version.json contains invalid JSON."""
        # Expected
        expected_default = {"version": "0.0.0-none", "changes": []}

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True

            mock_version_file.open.return_value = mock_open(
                read_data="invalid json content"
            ).return_value

            # Match against expected
            result = await version()
            assert isinstance(result, dict)
            assert result == expected_default

    @pytest.mark.asyncio
    async def test_version_endpoint_file_permission_error(self):
        """Test version endpoint when file reading raises a permission error."""
        # Expected
        expected_default = {"version": "0.0.0-none", "changes": []}

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True

            mock_version_file.open.side_effect = PermissionError("Permission denied")

            # Match against expected
            result = await version()
            assert isinstance(result, dict)
            assert result == expected_default

    @pytest.mark.asyncio
    async def test_version_endpoint_unexpected_exception(self):
        """Test version endpoint when an unexpected exception occurs."""
        # Expected
        expected_default = {"version": "0.0.0-none", "changes": []}

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True

            mock_version_file.open.side_effect = Exception("Unexpected error")

            # Match against expected
            result = await version()
            assert isinstance(result, dict)
            assert result == expected_default

    @pytest.mark.asyncio
    async def test_version_endpoint_uses_correct_file_path(self):
        """Test that version endpoint attempts to read from the correct file path."""
        # Expected
        expected_default = {"version": "0.0.0-none", "changes": []}

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = False

            # Match against expected
            result = await version()
            mock_path.assert_called_once_with("version.json")
            mock_version_file.is_file.assert_called_once()
            assert isinstance(result, dict)
            assert result == expected_default


class TestVersionEndpointHTTP:
    """Test cases for the /api/version HTTP endpoint using TestClient."""

    def test_version_endpoint_http_success(self, client):
        """Test version endpoint via HTTP with valid version file."""
        # Expected
        expected_version_data = {
            "version": "1.0.0",
            "sha": "testsha123",
            "branch": "test-branch",
            "changes": [],
        }

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True
            mock_file_content = json.dumps(expected_version_data)
            mock_version_file.open.return_value = mock_open(
                read_data=mock_file_content
            ).return_value

            # Match against expected
            response = client.get("/api/version")
            assert response.status_code == 200
            assert isinstance(response.json(), dict)
            assert response.json() == expected_version_data

    def test_version_endpoint_http_no_file(self, client):
        """Test version endpoint via HTTP when version file doesn't exist."""
        # Expected
        expected_default = {"version": "0.0.0-none", "changes": []}

        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = False

            # Match against expected
            response = client.get("/api/version")
            assert response.status_code == 200
            assert isinstance(response.json(), dict)
            assert response.json() == expected_default


class TestAPIRouterConfiguration:
    """Test cases for the API router configuration."""

    def test_router_includes_all_expected_routers(self):
        """Test that the main router includes all expected sub-routers."""
        # Act - Get all routes from the router
        routes = [route.path for route in router.routes if hasattr(route, "path")]

        # Assert - Verify router functionality and structure
        assert router is not None
        assert isinstance(routes, list)
        assert len(routes) >= 1

        # Check that the version endpoint is included
        version_routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and route.path == "/api/version"
        ]
        assert len(version_routes) == 1

    def test_version_endpoint_metadata(self):
        """Test that the version endpoint has correct metadata and configuration."""
        # Act - Find the version endpoint
        version_routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and route.path == "/api/version"
        ]

        # Assert - Verify endpoint configuration
        assert len(version_routes) == 1

        version_route = version_routes[0]
        assert hasattr(version_route, "methods")
        assert "GET" in version_route.methods
        # Ensure it only accepts GET requests for version info
        assert (
            len([method for method in version_route.methods if method != "HEAD"]) == 1
        )
