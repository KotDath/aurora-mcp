"""Tests for Figma API client functionality."""

from unittest.mock import Mock, patch

import pytest

from aurora_mcp.utils.figma_client import (
    FigmaClient,
    FigmaDataExtractor,
    extract_file_key_from_url,
    validate_figma_access_token,
)


class TestFigmaClient:
    """Test cases for FigmaClient class."""

    def test_client_initialization(self):
        """Test FigmaClient initialization."""
        token = "figd_test_token_123"
        client = FigmaClient(token)

        assert client.access_token == token
        assert client.base_url == "https://api.figma.com/v1"
        assert client.headers["X-Figma-Token"] == token

    @patch("aurora_mcp.utils.figma_client.requests")
    def test_fetch_file_success(self, mock_requests):
        """Test successful file fetching."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"name": "Test File", "document": {}}
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        client = FigmaClient("test_token")
        result = client.fetch_file("ABC123")

        assert result["name"] == "Test File"
        mock_requests.get.assert_called_once()

    @patch("aurora_mcp.utils.figma_client.requests")
    def test_fetch_file_failure(self, mock_requests):
        """Test file fetching failure."""
        mock_requests.get.side_effect = Exception("Network error")

        client = FigmaClient("test_token")

        with pytest.raises(Exception) as exc_info:
            client.fetch_file("ABC123")

        assert "Failed to fetch Figma file" in str(exc_info.value)

    def test_extract_all_metadata(self):
        """Test metadata extraction."""
        client = FigmaClient("test_token")

        file_data = {
            "name": "Test File",
            "document": {"type": "DOCUMENT"},
            "components": {},
            "lastModified": "2025-01-01T00:00:00Z",
        }

        metadata = client.extract_all_metadata(file_data)

        assert metadata["name"] == "Test File"
        assert metadata["document"]["type"] == "DOCUMENT"
        assert "lastModified" in metadata


class TestUrlExtraction:
    """Test cases for URL and file key extraction."""

    def test_extract_file_key_from_url_valid(self):
        """Test file key extraction from valid URLs."""
        test_cases = [
            ("https://www.figma.com/file/ABC123/title", "ABC123"),
            ("https://www.figma.com/file/XYZ789/title?node-id=1%3A2", "XYZ789"),
            ("https://www.figma.com/design/DEF456/title", "DEF456"),
            ("https://figma.com/file/GHI789/title", "GHI789"),
        ]

        for url, expected_key in test_cases:
            result = extract_file_key_from_url(url)
            assert result == expected_key

    def test_extract_file_key_from_url_invalid(self):
        """Test file key extraction from invalid URLs."""
        invalid_urls = [
            "https://example.com/file/ABC123",
            "not-a-url",
            "https://figma.com/random/path",
            "",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError):
                extract_file_key_from_url(url)


class TestTokenValidation:
    """Test cases for access token validation."""

    def test_validate_figma_access_token_valid(self):
        """Test validation of valid tokens."""
        valid_tokens = [
            "figd_" + "a" * 60,  # Modern token format
            "figd_ABC123DEF456GHI789" + "x" * 40,  # Realistic token
            "legacy-token-" + "x" * 40,  # Legacy format
        ]

        for token in valid_tokens:
            assert validate_figma_access_token(token) is True

    def test_validate_figma_access_token_invalid(self):
        """Test validation of invalid tokens."""
        invalid_tokens = ["", "short", "invalid-format", "figd_too_short", None]

        for token in invalid_tokens:
            assert validate_figma_access_token(token) is False


class TestFigmaDataExtractor:
    """Test cases for FigmaDataExtractor utilities."""

    def test_extract_text_content(self):
        """Test text content extraction."""
        text_node = {"type": "TEXT", "characters": "Hello World"}

        result = FigmaDataExtractor.extract_text_content(text_node)
        assert result == "Hello World"

        non_text_node = {"type": "RECTANGLE"}

        result = FigmaDataExtractor.extract_text_content(non_text_node)
        assert result is None

    def test_extract_fill_colors(self):
        """Test fill color extraction."""
        node_with_fills = {
            "fills": [
                {
                    "type": "SOLID",
                    "visible": True,
                    "color": {"r": 1.0, "g": 0.5, "b": 0.0, "a": 1.0},
                },
                {
                    "type": "SOLID",
                    "visible": True,
                    "color": {"r": 0.0, "g": 0.0, "b": 1.0, "a": 0.5},
                },
            ]
        }

        colors = FigmaDataExtractor.extract_fill_colors(node_with_fills)
        assert len(colors) == 2
        assert "#ff8000" in colors[0]  # Orange color
        assert "rgba(0, 0, 255, 0.5)" in colors[1]  # Blue with alpha

    def test_extract_bounds(self):
        """Test bounds extraction."""
        node_with_bounds = {
            "absoluteBoundingBox": {"x": 100, "y": 200, "width": 150, "height": 75}
        }

        bounds = FigmaDataExtractor.extract_bounds(node_with_bounds)

        assert bounds["x"] == 100
        assert bounds["y"] == 200
        assert bounds["width"] == 150
        assert bounds["height"] == 75

    def test_has_auto_layout(self):
        """Test auto layout detection."""
        auto_layout_node = {"layoutMode": "HORIZONTAL", "itemSpacing": 10}

        assert FigmaDataExtractor.has_auto_layout(auto_layout_node) is True

        manual_layout_node = {"layoutMode": "NONE"}

        assert FigmaDataExtractor.has_auto_layout(manual_layout_node) is False

        no_layout_node = {}

        assert FigmaDataExtractor.has_auto_layout(no_layout_node) is False

    def test_extract_auto_layout_info(self):
        """Test auto layout information extraction."""
        auto_layout_node = {
            "layoutMode": "VERTICAL",
            "primaryAxisSizingMode": "AUTO",
            "itemSpacing": 16,
            "paddingLeft": 8,
            "paddingTop": 12,
        }

        layout_info = FigmaDataExtractor.extract_auto_layout_info(auto_layout_node)

        assert layout_info["layoutMode"] == "VERTICAL"
        assert layout_info["itemSpacing"] == 16
        assert layout_info["paddingLeft"] == 8
        assert layout_info["paddingTop"] == 12

        # Test node without auto layout
        manual_node = {"layoutMode": "NONE"}
        layout_info = FigmaDataExtractor.extract_auto_layout_info(manual_node)
        assert layout_info == {}


# Integration test
@pytest.mark.integration
def test_figma_client_integration():
    """Integration test for FigmaClient (requires real token and file)."""
    # This test is marked as integration and would require real credentials
    # Skip in regular test runs
    pytest.skip("Integration test requires real Figma credentials")


if __name__ == "__main__":
    pytest.main([__file__])
