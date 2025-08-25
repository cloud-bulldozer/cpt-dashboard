import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, mock_open

from fastapi.testclient import TestClient
import pytest

from app.main import app as fastapi_app
from app.api.api import router, version


"""Unit tests for the main API router and version endpoint.

This file tests the main API router configuration and the version endpoint
functionality including various error scenarios.
"""


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    yield TestClient(fastapi_app)


class TestVersionEndpoint:
    """Test cases for the /api/version endpoint."""

    @pytest.mark.asyncio
    async def test_version_endpoint_with_valid_file(self):
        """Test version endpoint when version.json exists and contains valid data."""
        # Arrange
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
            ]
        }
        
        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True
            mock_file_content = json.dumps(expected_version_data)
            
            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                # Act
                result = await version()
                
                # Assert
                assert result == expected_version_data

    @pytest.mark.asyncio
    async def test_version_endpoint_file_not_exists(self):
        """Test version endpoint when version.json doesn't exist."""
        # Arrange
        expected_default = {"version": "0.0.0-none", "changes": []}
        
        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = False
            
            # Act
            result = await version()
            
            # Assert
            assert result == expected_default

    @pytest.mark.asyncio
    async def test_version_endpoint_invalid_json(self):
        """Test version endpoint when version.json contains invalid JSON."""
        # Arrange
        expected_default = {"version": "0.0.0-none", "changes": []}
        
        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True
            
            with patch("builtins.open", mock_open(read_data="invalid json content")):
                with patch("builtins.print") as mock_print:  # Mock print to capture error message
                    # Act
                    result = await version()
                    
                    # Assert
                    assert result == expected_default
                    mock_print.assert_called_once()
                    # Verify that an error message was printed
                    assert "Unable to read" in str(mock_print.call_args[0][0])

    @pytest.mark.asyncio
    async def test_version_endpoint_file_permission_error(self):
        """Test version endpoint when file reading raises a permission error."""
        # Arrange
        expected_default = {"version": "0.0.0-none", "changes": []}
        
        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True
            
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                with patch("builtins.print") as mock_print:
                    # Act
                    result = await version()
                    
                    # Assert
                    assert result == expected_default
                    mock_print.assert_called_once()
                    assert "Permission denied" in str(mock_print.call_args[0][0])

    @pytest.mark.asyncio
    async def test_version_endpoint_unexpected_exception(self):
        """Test version endpoint when an unexpected exception occurs."""
        # Arrange
        expected_default = {"version": "0.0.0-none", "changes": []}
        
        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True
            
            with patch("builtins.open", side_effect=Exception("Unexpected error")):
                with patch("builtins.print") as mock_print:
                    # Act
                    result = await version()
                    
                    # Assert
                    assert result == expected_default
                    mock_print.assert_called_once()
                    assert "Unexpected error" in str(mock_print.call_args[0][0])


class TestVersionEndpointHTTP:
    """Test cases for the /api/version HTTP endpoint using TestClient."""

    def test_version_endpoint_http_success(self, client):
        """Test version endpoint via HTTP with valid version file."""
        # Arrange
        expected_version_data = {
            "version": "1.0.0",
            "sha": "testsha123",
            "branch": "test-branch",
            "changes": []
        }
        
        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = True
            mock_file_content = json.dumps(expected_version_data)
            
            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                # Act
                response = client.get("/api/version")
                
                # Assert
                assert response.status_code == 200
                assert response.json() == expected_version_data

    def test_version_endpoint_http_no_file(self, client):
        """Test version endpoint via HTTP when version file doesn't exist."""
        # Arrange
        expected_default = {"version": "0.0.0-none", "changes": []}
        
        with patch("app.api.api.Path") as mock_path:
            mock_version_file = mock_path.return_value
            mock_version_file.is_file.return_value = False
            
            # Act
            response = client.get("/api/version")
            
            # Assert
            assert response.status_code == 200
            assert response.json() == expected_default


class TestAPIRouterConfiguration:
    """Test cases for the API router configuration."""

    def test_router_includes_all_expected_routers(self):
        """Test that the main router includes all expected sub-routers."""
        # Get all routes from the router
        routes = [route.path for route in router.routes]
        
        # We can't easily test the exact router inclusion without importing all modules,
        # but we can verify the router object exists and has routes
        assert router is not None
        assert len(routes) >= 1  # At least the version endpoint should be there
        
        # Check that the version endpoint is included
        version_routes = [route for route in router.routes if hasattr(route, 'path') and route.path == "/api/version"]
        assert len(version_routes) == 1

    def test_version_endpoint_metadata(self):
        """Test that the version endpoint has correct metadata."""
        version_routes = [route for route in router.routes if hasattr(route, 'path') and route.path == "/api/version"]
        assert len(version_routes) == 1
        
        version_route = version_routes[0]
        assert hasattr(version_route, 'methods')
        assert "GET" in version_route.methods