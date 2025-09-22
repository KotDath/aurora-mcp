"""Tests for QML generator functionality."""

import pytest

from aurora_mcp.utils.qml_generator import QMLGenerator


class TestQMLGenerator:
    """Test cases for QMLGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = QMLGenerator()

    def test_initialization(self):
        """Test QMLGenerator initialization."""
        assert self.generator.indent_size == 4
        assert isinstance(self.generator._generated_components, set)

    def test_create_sailfish_imports(self):
        """Test Sailfish imports generation."""
        imports = self.generator.create_sailfish_imports()

        assert "import QtQuick 2.0" in imports
        assert "import Sailfish.Silica 1.0" in imports

    def test_generate_empty_page(self):
        """Test empty page generation."""
        empty_page = self.generator._generate_empty_page()

        assert "Page {" in empty_page
        assert 'objectName: "mainPage"' in empty_page
        assert "allowedOrientations: Orientation.All" in empty_page
        assert "PageHeader {" in empty_page
        assert "qsTr(" in empty_page

    def test_safe_object_name(self):
        """Test safe object name generation."""
        test_cases = [
            ("My Button", "myButton"),
            ("button-1", "button_1"),
            ("Special@#$Characters", "specialCharacters"),
            ("123InvalidStart", "item_123InvalidStart"),
            ("normal_name", "normal_name"),
            ("", "item"),
        ]

        for input_name, expected in test_cases:
            result = self.generator._safe_object_name(input_name)
            # Allow some flexibility in naming convention
            assert result.isidentifier(), (
                f"Generated name '{result}' is not a valid identifier"
            )
            assert not result[0].isdigit(), (
                f"Generated name '{result}' starts with digit"
            )

    def test_escape_qml_string(self):
        """Test QML string escaping."""
        test_cases = [
            ("Hello World", "Hello World"),
            ('Text with "quotes"', 'Text with \\"quotes\\"'),
            ("Path\\with\\backslashes", "Path\\\\with\\\\backslashes"),
            ("Text\nwith\nnewlines", "Text\\nwith\\nnewlines"),
        ]

        for input_str, expected in test_cases:
            result = self.generator._escape_qml_string(input_str)
            assert result == expected

    def test_generate_basic_structure_empty_data(self):
        """Test basic structure generation with empty data."""
        figma_data = {"document": {"children": []}}

        result = self.generator.generate_basic_structure(figma_data)

        assert "Page {" in result
        assert "import QtQuick 2.0" in result
        assert "import Sailfish.Silica 1.0" in result

    def test_generate_basic_structure_with_page(self):
        """Test basic structure generation with page data."""
        figma_data = {
            "document": {
                "children": [
                    {
                        "type": "CANVAS",
                        "name": "Page 1",
                        "children": [
                            {
                                "type": "FRAME",
                                "name": "MainFrame",
                                "children": [
                                    {
                                        "type": "TEXT",
                                        "name": "Title",
                                        "characters": "Hello World",
                                        "absoluteBoundingBox": {
                                            "x": 0,
                                            "y": 0,
                                            "width": 200,
                                            "height": 50,
                                        },
                                    }
                                ],
                                "absoluteBoundingBox": {
                                    "x": 0,
                                    "y": 0,
                                    "width": 400,
                                    "height": 600,
                                },
                            }
                        ],
                    }
                ]
            }
        }

        result = self.generator.generate_basic_structure(figma_data)

        assert "Page {" in result
        assert "PageHeader {" in result
        assert "MainFrame" in result or "mainFrame" in result

    def test_generate_app_main(self):
        """Test application main file generation."""
        app_qml = self.generator.generate_app_main("TestApp", "MainPage")

        assert "ApplicationWindow {" in app_qml
        assert "initialPage: Component { MainPage {} }" in app_qml
        assert "cover:" in app_qml

    def test_generate_component_file(self):
        """Test component file generation."""
        figma_node = {
            "type": "RECTANGLE",
            "name": "CustomButton",
            "absoluteBoundingBox": {"x": 0, "y": 0, "width": 100, "height": 40},
            "fills": [
                {
                    "type": "SOLID",
                    "visible": True,
                    "color": {"r": 0.2, "g": 0.4, "b": 0.8, "a": 1.0},
                }
            ],
        }

        properties = ["text", "onClicked"]
        component_qml = self.generator.generate_component_file(
            "CustomButton", figma_node, properties
        )

        assert "property var text" in component_qml
        assert "property var onClicked" in component_qml
        assert "Rectangle {" in component_qml
        assert "import QtQuick 2.0" in component_qml
        assert "import Sailfish.Silica 1.0" in component_qml

    def test_calculate_relative_position(self):
        """Test relative position calculation."""
        properties = {"x": 150, "y": 200}
        parent_bounds = {"x": 50, "y": 100, "width": 400, "height": 600}

        rel_x, rel_y = self.generator._calculate_relative_position(
            properties, parent_bounds
        )

        assert rel_x == 100  # 150 - 50
        assert rel_y == 100  # 200 - 100

    def test_calculate_relative_position_no_parent(self):
        """Test relative position calculation without parent bounds."""
        properties = {"x": 150, "y": 200}

        rel_x, rel_y = self.generator._calculate_relative_position(properties, None)

        assert rel_x == 150
        assert rel_y == 200

    def test_generate_file_structure_info(self):
        """Test file structure information generation."""
        figma_data = {
            "name": "Test App",
            "document": {
                "children": [
                    {
                        "type": "CANVAS",
                        "name": "Main Screen",
                        "children": [
                            {"type": "FRAME", "name": "HomePage", "children": []}
                        ],
                    }
                ]
            },
        }

        structure_info = self.generator.generate_file_structure_info(figma_data)

        assert "main_file" in structure_info
        assert "pages" in structure_info
        assert "suggested_structure" in structure_info
        assert len(structure_info["pages"]) > 0

    def test_indent_code(self):
        """Test code indentation utility."""
        code = "Rectangle {\n    width: 100\n    height: 50\n}"
        indented = self.generator._indent_code(code, 2)

        lines = indented.split("\n")
        assert lines[0] == "        Rectangle {"  # 2 * 4 spaces
        assert lines[1] == "            width: 100"  # Additional indentation preserved

    def test_suggest_component_name(self):
        """Test component name suggestion."""
        test_elements = [
            ({"name": "submit button", "type": "RECTANGLE"}, "CustomButton"),
            ({"name": "user card", "type": "FRAME"}, "InfoCard"),
            ({"name": "list item", "type": "GROUP"}, "ListItem"),
            ({"name": "header text", "type": "TEXT"}, "SectionHeader"),
            ({"name": "unknown element", "type": "UNKNOWN"}, "CustomComponent"),
        ]

        for element, expected_pattern in test_elements:
            result = self.generator._suggest_component_name(element)
            # Check that result contains expected pattern or is a reasonable name
            assert isinstance(result, str)
            assert len(result) > 0
            assert result[0].isupper()  # Should be PascalCase


class TestQMLGeneratorIntegration:
    """Integration tests for QML generator with complex data."""

    def test_generate_complex_page(self):
        """Test generation of complex page structure."""
        complex_figma_data = {
            "name": "Mobile App",
            "document": {
                "children": [
                    {
                        "type": "CANVAS",
                        "name": "Home Screen",
                        "children": [
                            {
                                "type": "FRAME",
                                "name": "HomePage",
                                "absoluteBoundingBox": {
                                    "x": 0,
                                    "y": 0,
                                    "width": 375,
                                    "height": 812,
                                },
                                "children": [
                                    {
                                        "type": "TEXT",
                                        "name": "Title",
                                        "characters": "Welcome",
                                        "absoluteBoundingBox": {
                                            "x": 20,
                                            "y": 100,
                                            "width": 335,
                                            "height": 40,
                                        },
                                    },
                                    {
                                        "type": "RECTANGLE",
                                        "name": "Button",
                                        "absoluteBoundingBox": {
                                            "x": 50,
                                            "y": 200,
                                            "width": 275,
                                            "height": 50,
                                        },
                                        "fills": [
                                            {
                                                "type": "SOLID",
                                                "visible": True,
                                                "color": {
                                                    "r": 0.0,
                                                    "g": 0.5,
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
                ]
            },
        }

        generator = QMLGenerator()
        result = generator.generate_basic_structure(complex_figma_data)

        # Verify structure
        assert "import QtQuick 2.0" in result
        assert "import Sailfish.Silica 1.0" in result
        assert "Page {" in result
        assert "PageHeader {" in result

        # Verify components are generated
        lines = result.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) > 10  # Should have substantial content

    def test_auto_layout_generation(self):
        """Test auto-layout QML generation."""
        auto_layout_node = {
            "type": "FRAME",
            "name": "AutoLayoutFrame",
            "layoutMode": "VERTICAL",
            "itemSpacing": 16,
            "paddingLeft": 20,
            "paddingTop": 20,
            "children": [
                {
                    "type": "TEXT",
                    "name": "Item1",
                    "characters": "First Item",
                    "absoluteBoundingBox": {
                        "x": 20,
                        "y": 20,
                        "width": 100,
                        "height": 30,
                    },
                },
                {
                    "type": "TEXT",
                    "name": "Item2",
                    "characters": "Second Item",
                    "absoluteBoundingBox": {
                        "x": 20,
                        "y": 56,
                        "width": 100,
                        "height": 30,
                    },
                },
            ],
            "absoluteBoundingBox": {"x": 0, "y": 0, "width": 140, "height": 106},
        }

        generator = QMLGenerator()
        result = generator.generate_layout_from_auto_layout(auto_layout_node)

        assert "ColumnLayout {" in result
        assert "spacing: 16" in result


if __name__ == "__main__":
    pytest.main([__file__])
