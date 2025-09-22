"""QML code validator for checking syntax and Sailfish guidelines."""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """Container for validation results."""

    syntax_valid: bool = True
    errors: list[str] = None
    warnings: list[str] = None
    suggestions: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []

    def add_error(self, message: str):
        """Add an error to the results."""
        self.errors.append(message)
        self.syntax_valid = False

    def add_warning(self, message: str):
        """Add a warning to the results."""
        self.warnings.append(message)

    def add_suggestion(self, message: str):
        """Add a suggestion to the results."""
        self.suggestions.append(message)

    def has_issues(self) -> bool:
        """Check if there are any validation issues."""
        return bool(self.errors or self.warnings)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "syntax_valid": self.syntax_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "has_issues": self.has_issues(),
        }


class QMLValidator:
    """Validator for QML code syntax and Sailfish guidelines."""

    def __init__(self):
        self.sailfish_components = {
            "Page",
            "PageHeader",
            "SilicaListView",
            "SilicaFlickable",
            "Label",
            "Button",
            "TextField",
            "TextArea",
            "IconButton",
            "PullDownMenu",
            "PushUpMenu",
            "MenuItem",
            "ContextMenu",
            "Dialog",
            "TextSwitch",
            "Slider",
            "ProgressBar",
            "BusyIndicator",
            "ApplicationWindow",
            "Cover",
            "CoverPage",
        }

        self.required_imports = ["import QtQuick 2.0", "import Sailfish.Silica 1.0"]

        self.optional_imports = [
            "import QtQuick.Layouts 1.0",
            "import QtGraphicalEffects 1.0",
            "import QtMultimedia 5.0",
        ]

        # QML keywords that shouldn't be used as identifiers
        self.qml_keywords = {
            "import",
            "as",
            "property",
            "signal",
            "function",
            "readonly",
            "default",
            "alias",
            "var",
            "bool",
            "int",
            "real",
            "double",
            "string",
            "url",
            "color",
            "date",
            "variant",
            "Component",
            "Item",
            "Rectangle",
            "Text",
            "Image",
            "MouseArea",
        }

    def validate_syntax(self, qml_code: str) -> dict[str, Any]:
        """
        Perform comprehensive QML validation.

        Args:
            qml_code: QML code to validate

        Returns:
            Dictionary with validation results
        """
        result = ValidationResult()

        # Basic syntax checks
        self._check_imports(qml_code, result)
        self._check_brackets(qml_code, result)
        self._check_property_syntax(qml_code, result)
        self._check_string_literals(qml_code, result)

        # Sailfish-specific checks
        self._check_sailfish_guidelines(qml_code, result)
        self._check_naming_conventions(qml_code, result)
        self._check_theme_usage(qml_code, result)
        self._check_accessibility(qml_code, result)

        # Performance and best practices
        self._check_performance_issues(qml_code, result)
        self._check_responsive_design(qml_code, result)

        return result.to_dict()

    def _check_imports(self, qml_code: str, result: ValidationResult):
        """Check for required and recommended imports."""
        lines = qml_code.split("\n")
        imports = [line.strip() for line in lines if line.strip().startswith("import")]

        # Check required imports
        for required_import in self.required_imports:
            if not any(required_import in imp for imp in imports):
                result.add_warning(f"Missing recommended import: {required_import}")

        # Check for deprecated imports
        deprecated_patterns = [
            (r"import QtQuick 1\.\d+", "Consider upgrading to QtQuick 2.0"),
            (
                r"import Sailfish\.Silica 0\.\d+",
                "Consider upgrading to Sailfish.Silica 1.0",
            ),
        ]

        for pattern, message in deprecated_patterns:
            if any(re.search(pattern, imp) for imp in imports):
                result.add_warning(message)

    def _check_brackets(self, qml_code: str, result: ValidationResult):
        """Check bracket balance and nesting."""
        open_braces = qml_code.count("{")
        close_braces = qml_code.count("}")

        if open_braces != close_braces:
            result.add_error(
                f"Unbalanced braces: {open_braces} open, {close_braces} close"
            )

        # Check for common bracket issues
        lines = qml_code.split("\n")
        brace_stack = []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # Track brace nesting
            for char in line:
                if char == "{":
                    brace_stack.append(line_num)
                elif char == "}":
                    if not brace_stack:
                        result.add_error(f"Line {line_num}: Unexpected closing brace")
                    else:
                        brace_stack.pop()

            # Check for missing semicolons in property assignments
            if (
                ":" in stripped
                and not stripped.endswith(("{", "}", ","))
                and not stripped.startswith("//")
            ):
                if re.match(r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:", stripped):
                    # This is a property assignment, should usually end with a value
                    if not re.search(r'["\d\w\])]$', stripped):
                        result.add_warning(
                            f"Line {line_num}: Property assignment might be incomplete"
                        )

    def _check_property_syntax(self, qml_code: str, result: ValidationResult):
        """Check property declarations and assignments."""
        # Check property declarations
        property_pattern = r"property\s+(\w+)\s+(\w+)(?:\s*:\s*(.+))?"
        for match in re.finditer(property_pattern, qml_code):
            prop_type, prop_name, prop_value = match.groups()

            # Check property naming
            if not re.match(r"^[a-z][a-zA-Z0-9]*$", prop_name):
                result.add_warning(
                    f"Property '{prop_name}' should use camelCase naming"
                )

            # Check for reserved keywords
            if prop_name in self.qml_keywords:
                result.add_error(f"Property name '{prop_name}' is a reserved keyword")

        # Check id declarations
        id_pattern = r"id\s*:\s*(\w+)"
        ids_used = set()
        for match in re.finditer(id_pattern, qml_code):
            id_name = match.group(1)

            # Check for duplicate IDs
            if id_name in ids_used:
                result.add_error(f"Duplicate ID '{id_name}' found")
            ids_used.add(id_name)

            # Check ID naming convention
            if not re.match(r"^[a-z][a-zA-Z0-9]*$", id_name):
                result.add_warning(
                    f"ID '{id_name}' should use camelCase and start with lowercase"
                )

    def _check_string_literals(self, qml_code: str, result: ValidationResult):
        """Check string literals for common issues."""
        # Find all string literals
        string_pattern = r'"([^"\\]|\\.)*"'
        re.findall(string_pattern, qml_code)

        # Check for unlocalized strings
        text_assignments = re.findall(r'text\s*:\s*"([^"]+)"', qml_code)
        for text in text_assignments:
            if text and not text.startswith("qsTr("):
                result.add_warning(f"Text '{text}' should use qsTr() for localization")

        # Check for hardcoded file paths
        file_path_pattern = r'"[./\\][\w./\\-]+"'
        for match in re.finditer(file_path_pattern, qml_code):
            path = match.group(0)
            if not any(
                prefix in path for prefix in ["qrc:", "image:", "Qt.resolvedUrl"]
            ):
                result.add_suggestion(
                    f"Consider using Qt.resolvedUrl() for file path {path}"
                )

    def _check_sailfish_guidelines(self, qml_code: str, result: ValidationResult):
        """Check compliance with Sailfish UI guidelines."""
        # Check for Page components
        if "Page {" in qml_code:
            if "objectName:" not in qml_code:
                result.add_warning("Page should have objectName property for debugging")

            if "allowedOrientations:" not in qml_code:
                result.add_suggestion("Consider adding allowedOrientations to Page")

            # Check for PageHeader
            if "PageHeader" not in qml_code:
                result.add_suggestion(
                    "Consider adding PageHeader to Page for consistent navigation"
                )

        # Check Theme usage
        if any(color in qml_code for color in ["color:", "border.color:"]):
            if "Theme." not in qml_code:
                result.add_warning(
                    "Consider using Theme colors instead of hardcoded colors"
                )

        # Check for proper list usage
        if "ListView" in qml_code and "SilicaListView" not in qml_code:
            result.add_suggestion(
                "Consider using SilicaListView instead of ListView for better Sailfish integration"
            )

        # Check for proper flickable usage
        if "Flickable" in qml_code and "SilicaFlickable" not in qml_code:
            result.add_suggestion(
                "Consider using SilicaFlickable instead of Flickable for better Sailfish integration"
            )

    def _check_naming_conventions(self, qml_code: str, result: ValidationResult):
        """Check QML naming conventions."""
        # Check property names
        property_matches = re.findall(r"property\s+\w+\s+(\w+)", qml_code)
        for prop_name in property_matches:
            if "_" in prop_name:
                result.add_suggestion(
                    f"Property '{prop_name}' should use camelCase instead of snake_case"
                )

        # Check function names
        function_matches = re.findall(r"function\s+(\w+)", qml_code)
        for func_name in function_matches:
            if not func_name[0].islower():
                result.add_warning(
                    f"Function '{func_name}' should start with lowercase letter"
                )

        # Check signal names
        signal_matches = re.findall(r"signal\s+(\w+)", qml_code)
        for signal_name in signal_matches:
            if not signal_name[0].islower():
                result.add_warning(
                    f"Signal '{signal_name}' should start with lowercase letter"
                )

    def _check_theme_usage(self, qml_code: str, result: ValidationResult):
        """Check proper Theme usage for Sailfish apps."""
        # Common hardcoded values that should use Theme
        hardcoded_checks = [
            (
                r"font\.pixelSize\s*:\s*\d+",
                "Consider using Theme.fontSizeSmall/Medium/Large",
            ),
            (
                r"spacing\s*:\s*\d+",
                "Consider using Theme.paddingSmall/Medium/Large for spacing",
            ),
            (
                r"anchors\.margins\s*:\s*\d+",
                "Consider using Theme.paddingMedium for margins",
            ),
            (
                r"width\s*:\s*Screen\.\w+",
                "Good use of Screen properties for responsive design",
            ),
        ]

        for pattern, message in hardcoded_checks:
            if re.search(pattern, qml_code):
                if "Consider" in message:
                    result.add_suggestion(message)
                else:
                    result.add_warning(message)

    def _check_accessibility(self, qml_code: str, result: ValidationResult):
        """Check accessibility considerations."""
        # Check for buttons without accessible descriptions
        button_pattern = r"(Button|IconButton)\s*\{"
        if re.search(button_pattern, qml_code):
            if "Accessible." not in qml_code:
                result.add_suggestion(
                    "Consider adding Accessible properties for better accessibility"
                )

        # Check for interactive elements with proper touch targets
        interactive_elements = ["MouseArea", "Button", "IconButton"]
        for element in interactive_elements:
            if element in qml_code:
                # This is a simplified check - real implementation would be more complex
                result.add_suggestion(
                    f"Ensure {element} has adequate touch target size (minimum 44x44)"
                )

    def _check_performance_issues(self, qml_code: str, result: ValidationResult):
        """Check for common performance issues."""
        # Check for excessive nesting
        max_nesting = 0
        current_nesting = 0
        for char in qml_code:
            if char == "{":
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif char == "}":
                current_nesting -= 1

        if max_nesting > 6:
            result.add_warning(
                f"Deep nesting detected ({max_nesting} levels). Consider refactoring into components."
            )

        # Check for potential binding loops
        if re.search(r"width\s*:\s*parent\.width\s*[+\-*/]", qml_code):
            result.add_suggestion(
                "Be careful with width calculations based on parent.width to avoid binding loops"
            )

        # Check for missing cached property for effects
        if any(effect in qml_code for effect in ["DropShadow", "Blur", "Glow"]):
            if "cached: true" not in qml_code:
                result.add_suggestion(
                    "Consider adding 'cached: true' to graphical effects for better performance"
                )

    def _check_responsive_design(self, qml_code: str, result: ValidationResult):
        """Check responsive design considerations."""
        # Check for Screen usage
        if "Screen." in qml_code:
            result.add_suggestion("Good use of Screen properties for responsive design")

        # Check for hardcoded sizes that might not scale well
        hardcoded_size_pattern = r"(width|height)\s*:\s*\d+"
        if re.search(hardcoded_size_pattern, qml_code):
            if "Screen." not in qml_code and "Theme." not in qml_code:
                result.add_warning(
                    "Consider using Screen or Theme properties for scalable dimensions"
                )

        # Check orientation handling
        if "Page {" in qml_code:
            if "orientation" not in qml_code:
                result.add_suggestion(
                    "Consider handling orientation changes for better user experience"
                )

    def validate_file_structure(self, file_paths: list[str]) -> dict[str, Any]:
        """
        Validate QML project file structure.

        Args:
            file_paths: List of QML file paths in the project

        Returns:
            Validation results for file structure
        """
        result = ValidationResult()

        # Check for main application file
        main_files = [f for f in file_paths if f.endswith(("Main.qml", "main.qml"))]
        if not main_files:
            result.add_warning("No main application file (Main.qml) found")

        # Check for proper directory structure
        has_pages = any("pages/" in path for path in file_paths)
        has_components = any("components/" in path for path in file_paths)

        if len(file_paths) > 3 and not has_pages:
            result.add_suggestion("Consider organizing QML files into pages/ directory")

        if len(file_paths) > 5 and not has_components:
            result.add_suggestion(
                "Consider creating reusable components in components/ directory"
            )

        # Check file naming conventions
        for path in file_paths:
            filename = path.split("/")[-1]
            if filename.endswith(".qml"):
                name_without_ext = filename[:-4]
                if not name_without_ext[0].isupper():
                    result.add_warning(
                        f"QML file '{filename}' should start with uppercase letter"
                    )

        return result.to_dict()

    def suggest_improvements(self, qml_code: str) -> list[str]:
        """
        Suggest specific improvements for QML code.

        Args:
            qml_code: QML code to analyze

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Analyze component structure
        if qml_code.count("{") > 10:
            suggestions.append(
                "Consider breaking down complex components into smaller, reusable parts"
            )

        # Check for modern QML patterns
        if "anchors.fill: parent" in qml_code and "Layout." not in qml_code:
            suggestions.append("Consider using Layouts for more flexible positioning")

        if "ListView" in qml_code:
            suggestions.append("Consider using delegate components for list items")

        # Performance suggestions
        if "Image {" in qml_code:
            suggestions.append("Consider using asynchronous: true for Image components")

        if any(anim in qml_code for anim in ["PropertyAnimation", "NumberAnimation"]):
            suggestions.append(
                "Ensure animations have reasonable duration and easing curves"
            )

        return suggestions

    def get_sailfish_compliance_score(self, qml_code: str) -> float:
        """
        Calculate a compliance score for Sailfish guidelines.

        Args:
            qml_code: QML code to score

        Returns:
            Compliance score from 0.0 to 1.0
        """
        score = 1.0
        validation = self.validate_syntax(qml_code)

        # Deduct points for errors and warnings
        score -= len(validation["errors"]) * 0.1
        score -= len(validation["warnings"]) * 0.05

        # Bonus points for good practices
        if "Theme." in qml_code:
            score += 0.1
        if "qsTr(" in qml_code:
            score += 0.1
        if any(comp in qml_code for comp in self.sailfish_components):
            score += 0.1
        if "Screen." in qml_code:
            score += 0.05

        return max(0.0, min(1.0, score))
