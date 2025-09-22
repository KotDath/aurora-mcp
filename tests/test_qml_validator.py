"""Tests for QML validator functionality."""

import pytest

from aurora_mcp.utils.qml_validator import QMLValidator, ValidationResult


class TestValidationResult:
    """Test cases for ValidationResult class."""

    def test_initialization_default(self):
        """Test ValidationResult default initialization."""
        result = ValidationResult()

        assert result.syntax_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []

    def test_initialization_with_data(self):
        """Test ValidationResult initialization with data."""
        result = ValidationResult(
            syntax_valid=False,
            errors=["Error 1"],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1"],
        )

        assert result.syntax_valid is False
        assert result.errors == ["Error 1"]
        assert result.warnings == ["Warning 1"]
        assert result.suggestions == ["Suggestion 1"]

    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult()
        result.add_error("Test error")

        assert "Test error" in result.errors
        assert result.syntax_valid is False

    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult()
        result.add_warning("Test warning")

        assert "Test warning" in result.warnings
        assert result.syntax_valid is True  # Warnings don't affect syntax validity

    def test_add_suggestion(self):
        """Test adding suggestions."""
        result = ValidationResult()
        result.add_suggestion("Test suggestion")

        assert "Test suggestion" in result.suggestions

    def test_has_issues(self):
        """Test has_issues method."""
        result = ValidationResult()
        assert result.has_issues() is False

        result.add_warning("Warning")
        assert result.has_issues() is True

        result = ValidationResult()
        result.add_error("Error")
        assert result.has_issues() is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ValidationResult()
        result.add_error("Error")
        result.add_warning("Warning")

        dict_result = result.to_dict()

        assert dict_result["syntax_valid"] is False
        assert "Error" in dict_result["errors"]
        assert "Warning" in dict_result["warnings"]
        assert dict_result["has_issues"] is True


class TestQMLValidator:
    """Test cases for QMLValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = QMLValidator()

    def test_initialization(self):
        """Test QMLValidator initialization."""
        assert len(self.validator.sailfish_components) > 0
        assert "Page" in self.validator.sailfish_components
        assert len(self.validator.required_imports) == 2

    def test_validate_syntax_valid_qml(self):
        """Test validation of valid QML code."""
        valid_qml = """import QtQuick 2.0
import Sailfish.Silica 1.0

Page {
    objectName: "mainPage"
    allowedOrientations: Orientation.All

    PageHeader {
        title: qsTr("Test Page")
    }

    Label {
        anchors.centerIn: parent
        text: qsTr("Hello World")
        color: Theme.primaryColor
    }
}"""

        result = self.validator.validate_syntax(valid_qml)

        assert result["syntax_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_syntax_invalid_brackets(self):
        """Test validation with unbalanced brackets."""
        invalid_qml = """Page {
    PageHeader {
        title: "Test"

}"""  # Missing closing brace

        result = self.validator.validate_syntax(invalid_qml)

        assert result["syntax_valid"] is False
        assert any("Unbalanced braces" in error for error in result["errors"])

    def test_check_imports_missing(self):
        """Test import checking with missing required imports."""
        qml_without_imports = """Page {
    title: "Test"
}"""

        result = self.validator.validate_syntax(qml_without_imports)

        warnings = result["warnings"]
        assert any(
            "Missing recommended import: import QtQuick 2.0" in warning
            for warning in warnings
        )
        assert any(
            "Missing recommended import: import Sailfish.Silica 1.0" in warning
            for warning in warnings
        )

    def test_check_sailfish_guidelines(self):
        """Test Sailfish guidelines checking."""
        qml_code = """import QtQuick 2.0
import Sailfish.Silica 1.0

Page {
    // Missing objectName and allowedOrientations

    Rectangle {
        color: "#ff0000"  // Hardcoded color instead of Theme
    }

    Text {
        text: "Hardcoded text"  // Should use qsTr()
    }
}"""

        result = self.validator.validate_syntax(qml_code)

        warnings = result["warnings"]
        suggestions = result["suggestions"]

        assert any("objectName" in warning for warning in warnings)
        assert any("Theme colors" in warning for warning in warnings)
        assert any("qsTr()" in warning for warning in warnings)
        assert any("allowedOrientations" in suggestion for suggestion in suggestions)

    def test_check_naming_conventions(self):
        """Test naming convention checking."""
        qml_code = """import QtQuick 2.0

Item {
    property string bad_property_name: "test"
    property string InvalidID: "test"

    function BadFunctionName() {}
    signal BadSignalName()

    id: BadIdName
}"""

        result = self.validator.validate_syntax(qml_code)

        warnings = result["warnings"]
        suggestions = result["suggestions"]

        # Check for naming convention issues
        assert any(
            "camelCase" in warning or "camelCase" in suggestions
            for warning in warnings + suggestions
        )

    def test_check_performance_issues(self):
        """Test performance issue detection."""
        # Generate deeply nested QML
        nested_qml = "Item {\n" * 10 + "}" * 10

        result = self.validator.validate_syntax(nested_qml)

        warnings = result["warnings"]
        assert any("nesting" in warning.lower() for warning in warnings)

    def test_check_responsive_design(self):
        """Test responsive design checking."""
        qml_with_hardcoded_sizes = """Page {
    Rectangle {
        width: 300
        height: 200
    }
}"""

        result = self.validator.validate_syntax(qml_with_hardcoded_sizes)

        warnings = result["warnings"]
        assert any("Screen or Theme properties" in warning for warning in warnings)

    def test_validate_file_structure(self):
        """Test file structure validation."""
        file_paths = [
            "qml/pages/MainPage.qml",
            "qml/pages/SettingsPage.qml",
            "qml/components/CustomButton.qml",
            "assets/images/icon.png",
        ]

        result = self.validator.validate_file_structure(file_paths)

        # Should suggest main file
        warnings = result["warnings"]
        assert any("main application file" in warning.lower() for warning in warnings)

    def test_validate_file_structure_good(self):
        """Test file structure validation with good structure."""
        file_paths = [
            "Main.qml",
            "qml/pages/MainPage.qml",
            "qml/pages/SettingsPage.qml",
            "qml/components/CustomButton.qml",
        ]

        result = self.validator.validate_file_structure(file_paths)

        # Should have fewer warnings with proper structure
        assert result["syntax_valid"] is True

    def test_suggest_improvements(self):
        """Test improvement suggestions."""
        complex_qml = """Page {
    Rectangle { width: 100; height: 100 }
    Rectangle { width: 100; height: 100 }
    Rectangle { width: 100; height: 100 }
    ListView {
        delegate: Rectangle {}
    }
    Image {
        source: "test.png"
    }
}"""

        suggestions = self.validator.suggest_improvements(complex_qml)

        assert len(suggestions) > 0
        assert any("component" in suggestion.lower() for suggestion in suggestions)

    def test_get_sailfish_compliance_score(self):
        """Test Sailfish compliance scoring."""
        good_qml = """import QtQuick 2.0
import Sailfish.Silica 1.0

Page {
    PageHeader {
        title: qsTr("Test")
    }

    Label {
        color: Theme.primaryColor
        text: qsTr("Content")
    }
}"""

        bad_qml = """Item {
    Rectangle {
        color: "#ff0000"
    }
    Text {
        text: "Bad text"
    }
}"""

        good_score = self.validator.get_sailfish_compliance_score(good_qml)
        bad_score = self.validator.get_sailfish_compliance_score(bad_qml)

        assert 0.0 <= good_score <= 1.0
        assert 0.0 <= bad_score <= 1.0
        assert good_score > bad_score

    def test_check_property_syntax(self):
        """Test property syntax checking."""
        qml_with_properties = """Item {
    property string validProperty: "test"
    property int invalid_property: 42
    property var import: "reserved"  // Reserved keyword

    id: validId
    id: duplicateId
    id: duplicateId  // Duplicate ID
}"""

        result = self.validator.validate_syntax(qml_with_properties)

        errors = result["errors"]
        result["warnings"]

        # Should detect reserved keyword usage
        assert any("reserved keyword" in error for error in errors)
        # Should detect duplicate IDs
        assert any("Duplicate ID" in error for error in errors)

    def test_check_string_literals(self):
        """Test string literal checking."""
        qml_code = """Text {
    text: "Unlocalized text"
    source: "./relative/path.png"
}"""

        result = self.validator.validate_syntax(qml_code)

        warnings = result["warnings"]
        suggestions = result["suggestions"]

        assert any("qsTr()" in warning for warning in warnings)
        assert any("Qt.resolvedUrl()" in suggestion for suggestion in suggestions)

    def test_check_theme_usage(self):
        """Test Theme usage checking."""
        qml_code = """Label {
    font.pixelSize: 16
    color: "#333333"

    anchors.margins: 8
}"""

        result = self.validator.validate_syntax(qml_code)

        suggestions = result["suggestions"]

        assert any("Theme.fontSize" in suggestion for suggestion in suggestions)
        assert any("Theme.padding" in suggestion for suggestion in suggestions)

    def test_check_accessibility(self):
        """Test accessibility checking."""
        qml_code = """Button {
    text: "Click me"
}

IconButton {
    icon.source: "icon.png"
}"""

        result = self.validator.validate_syntax(qml_code)

        suggestions = result["suggestions"]

        assert any("Accessible" in suggestion for suggestion in suggestions)
        assert any("touch target" in suggestion for suggestion in suggestions)


class TestQMLValidatorEdgeCases:
    """Test edge cases for QML validator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = QMLValidator()

    def test_empty_qml(self):
        """Test validation of empty QML."""
        result = self.validator.validate_syntax("")

        assert result["syntax_valid"] is True
        assert len(result["warnings"]) > 0  # Should warn about missing imports

    def test_qml_with_comments(self):
        """Test validation of QML with comments."""
        qml_with_comments = """// This is a comment
/* Multi-line
   comment */
Page {
    // Another comment
    title: "Test"
}"""

        result = self.validator.validate_syntax(qml_with_comments)

        assert result["syntax_valid"] is True

    def test_qml_with_complex_strings(self):
        """Test validation with complex string literals."""
        qml_code = """Text {
    text: "String with \\"quotes\\""
    property string multiline: "Line 1\\nLine 2"
    property url fileUrl: "file:///path/to/file.png"
}"""

        result = self.validator.validate_syntax(qml_code)

        # Should handle escaped quotes properly
        assert result["syntax_valid"] is True

    def test_very_long_qml(self):
        """Test validation of very long QML code."""
        # Generate long QML with many items
        long_qml = "import QtQuick 2.0\nItem {\n"
        for i in range(100):
            long_qml += f"    Rectangle {{ id: rect{i}; width: 10; height: 10 }}\n"
        long_qml += "}"

        result = self.validator.validate_syntax(long_qml)

        # Should handle long files
        assert isinstance(result, dict)
        assert "syntax_valid" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
