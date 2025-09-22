"""Tests for the main Figma to QML MCP tool."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aurora_mcp.tools.qt.figma_to_qml import (
    _count_nodes_recursive,
    _generate_conversion_report,
    _save_qml_project,
    _validate_inputs,
    figma_to_qml,
)


class TestFigmaToQMLTool:
    """Test cases for the main figma_to_qml tool."""

    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = _validate_inputs(
                figma_file_url="https://www.figma.com/file/ABC123/test",
                access_token="figd_" + "x" * 60,
                workspace_dir=temp_dir,
            )

            assert errors == []

    def test_validate_inputs_invalid_url(self):
        """Test input validation with invalid URL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = _validate_inputs(
                figma_file_url="https://example.com/invalid",
                access_token="figd_" + "x" * 60,
                workspace_dir=temp_dir,
            )

            assert len(errors) > 0
            assert any("Invalid Figma URL" in error for error in errors)

    def test_validate_inputs_invalid_token(self):
        """Test input validation with invalid token."""
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = _validate_inputs(
                figma_file_url="https://www.figma.com/file/ABC123/test",
                access_token="invalid_token",
                workspace_dir=temp_dir,
            )

            assert len(errors) > 0
            assert any("Invalid Figma access token" in error for error in errors)

    def test_validate_inputs_missing_params(self):
        """Test input validation with missing parameters."""
        errors = _validate_inputs("", "", "")

        assert len(errors) >= 3
        assert any("URL is required" in error for error in errors)
        assert any("access token is required" in error for error in errors)
        assert any("Workspace directory is required" in error for error in errors)

    def test_save_qml_project(self):
        """Test QML project file saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            enhanced_qml = """import QtQuick 2.0
import Sailfish.Silica 1.0

Page {
    objectName: "mainPage"

    PageHeader {
        title: qsTr("Test Page")
    }
}"""

            figma_data = {
                "name": "Test App",
                "lastModified": "2025-01-01T00:00:00Z",
                "version": "1.0",
            }

            validation_result = {
                "syntax_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
            }

            output_info = _save_qml_project(
                enhanced_qml=enhanced_qml,
                workspace_dir=temp_dir,
                figma_data=figma_data,
                validation_result=validation_result,
            )

            # Check that files were created
            assert Path(output_info["main_page"]).exists()
            assert Path(output_info["app_main"]).exists()
            assert Path(output_info["cover_page"]).exists()
            assert Path(output_info["readme"]).exists()

            # Check directory structure
            expected_dirs = ["qml/pages", "qml/components", "qml/cover"]
            for directory in expected_dirs:
                assert (Path(temp_dir) / directory).exists()

            # Check file contents
            with open(output_info["main_page"]) as f:
                content = f.read()
                assert "Page {" in content
                assert "PageHeader {" in content

    def test_generate_conversion_report(self):
        """Test conversion report generation."""
        figma_data = {
            "name": "Test Design",
            "lastModified": "2025-01-01T00:00:00Z",
            "version": "1.2.3",
            "document": {
                "children": [
                    {"type": "CANVAS", "children": [{"type": "FRAME", "children": []}]}
                ]
            },
        }

        enhanced_qml = "Page { }"
        validation_result = {
            "syntax_valid": True,
            "errors": [],
            "warnings": ["Test warning"],
            "suggestions": ["Test suggestion"],
        }

        output_info = {
            "main_page": "/test/MainPage.qml",
            "directories_created": ["qml/pages"],
        }

        report = _generate_conversion_report(
            figma_data=figma_data,
            enhanced_qml=enhanced_qml,
            validation_result=validation_result,
            workspace_dir="/test/workspace",
            enhancement_types=["auto_layout"],
            output_info=output_info,
        )

        assert "# Figma to QML Conversion Report" in report
        assert "Test Design" in report
        assert "auto_layout" in report
        assert "Test warning" in report
        assert "Test suggestion" in report

    def test_count_nodes_recursive(self):
        """Test recursive node counting."""
        document = {
            "type": "DOCUMENT",
            "children": [
                {
                    "type": "CANVAS",
                    "children": [
                        {"type": "FRAME", "children": []},
                        {
                            "type": "GROUP",
                            "children": [
                                {"type": "TEXT", "children": []},
                                {"type": "RECTANGLE", "children": []},
                            ],
                        },
                    ],
                }
            ],
        }

        count = _count_nodes_recursive(document)
        assert count == 6  # DOCUMENT + CANVAS + FRAME + GROUP + TEXT + RECTANGLE

    @patch("aurora_mcp.tools.qt.figma_to_qml.FigmaClient")
    @patch("aurora_mcp.tools.qt.figma_to_qml.extract_file_key_from_url")
    @patch("aurora_mcp.tools.qt.figma_to_qml.enhance_qml_code")
    def test_figma_to_qml_success_flow(
        self, mock_enhance_qml, mock_extract_key, mock_figma_client
    ):
        """Test successful figma_to_qml execution flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock setup
            mock_extract_key.return_value = "ABC123"

            mock_client_instance = Mock()
            mock_client_instance.fetch_file.return_value = {
                "name": "Test File",
                "document": {"children": []},
                "lastModified": "2025-01-01T00:00:00Z",
            }
            mock_client_instance.extract_all_metadata.return_value = {
                "name": "Test File",
                "document": {"children": []},
                "lastModified": "2025-01-01T00:00:00Z",
            }
            mock_figma_client.return_value = mock_client_instance

            mock_enhance_qml.return_value = """import QtQuick 2.0
import Sailfish.Silica 1.0

Page {
    objectName: "mainPage"
    allowedOrientations: Orientation.All

    PageHeader {
        title: qsTr("Test Page")
    }
}"""

            # Execute
            result = figma_to_qml(
                figma_file_url="https://www.figma.com/file/ABC123/test",
                access_token="figd_" + "x" * 60,
                workspace_dir=temp_dir,
                enhancement_types=["auto_layout"],
            )

            # Verify
            assert "✅ Conversion completed successfully!" in result
            assert temp_dir in result

            # Check that methods were called
            mock_extract_key.assert_called_once()
            mock_client_instance.fetch_file.assert_called_once_with("ABC123")
            mock_enhance_qml.assert_called()

    @patch("aurora_mcp.tools.qt.figma_to_qml.FigmaClient")
    def test_figma_to_qml_api_failure(self, mock_figma_client):
        """Test figma_to_qml handling of API failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock API failure
            mock_figma_client.side_effect = Exception("API Error")

            result = figma_to_qml(
                figma_file_url="https://www.figma.com/file/ABC123/test",
                access_token="figd_" + "x" * 60,
                workspace_dir=temp_dir,
            )

            assert "❌ Conversion failed:" in result
            assert "API Error" in result

    def test_figma_to_qml_validation_failure(self):
        """Test figma_to_qml with validation failures."""
        result = figma_to_qml(figma_file_url="", access_token="", workspace_dir="")

        assert "❌ Validation failed:" in result

    @patch("aurora_mcp.tools.qt.figma_to_qml.validate_figma_access_token")
    @patch("aurora_mcp.tools.qt.figma_to_qml.extract_file_key_from_url")
    def test_figma_to_qml_with_default_enhancement_types(
        self, mock_extract_key, mock_validate_token
    ):
        """Test figma_to_qml with default enhancement types."""
        mock_extract_key.return_value = "ABC123"
        mock_validate_token.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "aurora_mcp.tools.qt.figma_to_qml.FigmaClient"
            ) as mock_client_class:
                mock_client = Mock()
                mock_client.fetch_file.return_value = {
                    "name": "Test",
                    "document": {"children": []},
                }
                mock_client.extract_all_metadata.return_value = {
                    "name": "Test",
                    "document": {"children": []},
                }
                mock_client_class.return_value = mock_client

                with patch(
                    "aurora_mcp.tools.qt.figma_to_qml.enhance_qml_code"
                ) as mock_enhance:
                    mock_enhance.return_value = "Page { }"

                    # Call without enhancement_types - should use defaults
                    figma_to_qml(
                        figma_file_url="https://www.figma.com/file/ABC123/test",
                        access_token="figd_" + "x" * 60,
                        workspace_dir=temp_dir,
                    )

                    # Should use default enhancement types
                    assert mock_enhance.call_count >= 2  # auto_layout and components


class TestIntegration:
    """Integration tests for the complete tool."""

    @pytest.mark.integration
    def test_end_to_end_with_mock_data(self):
        """End-to-end test with comprehensive mock data."""
        mock_figma_response = {
            "name": "Mobile App Design",
            "lastModified": "2025-01-01T12:00:00Z",
            "version": "2.1.0",
            "document": {
                "type": "DOCUMENT",
                "children": [
                    {
                        "type": "CANVAS",
                        "name": "iPhone 14",
                        "children": [
                            {
                                "type": "FRAME",
                                "name": "HomeScreen",
                                "absoluteBoundingBox": {
                                    "x": 0,
                                    "y": 0,
                                    "width": 390,
                                    "height": 844,
                                },
                                "children": [
                                    {
                                        "type": "TEXT",
                                        "name": "Welcome Title",
                                        "characters": "Welcome to App",
                                        "absoluteBoundingBox": {
                                            "x": 20,
                                            "y": 100,
                                            "width": 350,
                                            "height": 50,
                                        },
                                    },
                                    {
                                        "type": "RECTANGLE",
                                        "name": "Login Button",
                                        "absoluteBoundingBox": {
                                            "x": 50,
                                            "y": 200,
                                            "width": 290,
                                            "height": 50,
                                        },
                                        "fills": [
                                            {
                                                "type": "SOLID",
                                                "visible": True,
                                                "color": {
                                                    "r": 0.2,
                                                    "g": 0.6,
                                                    "b": 1.0,
                                                    "a": 1.0,
                                                },
                                            }
                                        ],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "aurora_mcp.tools.qt.figma_to_qml.FigmaClient"
            ) as mock_client_class:
                with patch(
                    "aurora_mcp.tools.qt.figma_to_qml.extract_file_key_from_url"
                ) as mock_extract:
                    with patch(
                        "aurora_mcp.tools.qt.figma_to_qml.enhance_qml_code"
                    ) as mock_enhance:
                        # Setup mocks
                        mock_extract.return_value = "TESTKEY123"

                        mock_client = Mock()
                        mock_client.fetch_file.return_value = mock_figma_response
                        mock_client.extract_all_metadata.return_value = (
                            mock_figma_response
                        )
                        mock_client_class.return_value = mock_client

                        mock_enhance.return_value = """import QtQuick 2.0
import Sailfish.Silica 1.0

Page {
    objectName: "homeScreen"
    allowedOrientations: Orientation.All

    PageHeader {
        title: qsTr("Mobile App Design")
    }

    Text {
        anchors.centerIn: parent
        text: qsTr("Welcome to App")
        color: Theme.primaryColor
    }
}"""

                        # Execute
                        result = figma_to_qml(
                            figma_file_url="https://www.figma.com/file/TESTKEY123/mobile-app",
                            access_token="figd_" + "a" * 60,
                            workspace_dir=temp_dir,
                            enhancement_types=[
                                "auto_layout",
                                "components",
                                "responsive",
                            ],
                        )

                        # Verify success
                        assert "✅ Conversion completed successfully!" in result

                        # Verify files were created
                        assert (Path(temp_dir) / "qml" / "Main.qml").exists()
                        assert (
                            Path(temp_dir) / "qml" / "pages" / "MainPage.qml"
                        ).exists()
                        assert (
                            Path(temp_dir) / "qml" / "cover" / "CoverPage.qml"
                        ).exists()
                        assert (Path(temp_dir) / "README.md").exists()
                        assert (Path(temp_dir) / "conversion-report.md").exists()

                        # Verify content quality
                        with open(
                            Path(temp_dir) / "qml" / "pages" / "MainPage.qml"
                        ) as f:
                            qml_content = f.read()
                            assert "import QtQuick 2.0" in qml_content
                            assert "import Sailfish.Silica 1.0" in qml_content
                            assert "Page {" in qml_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
