"""QML code generator for converting Figma data to QML structure."""

from typing import Any


class QMLGenerator:
    """Generator for creating basic QML code from Figma data."""

    def __init__(self):
        self.indent_size = 4
        self._generated_components = set()  # Track generated component names

    def generate_basic_structure(self, figma_data: dict[str, Any]) -> str:
        """
        Generate basic QML structure from Figma data.

        Args:
            figma_data: Processed Figma file data

        Returns:
            Basic QML code string
        """
        document = figma_data.get("document", {})
        pages = document.get("children", [])

        if not pages:
            return self._generate_empty_page()

        # Take the first page as the main page
        main_page = pages[0]
        return self._generate_page_qml(main_page, figma_data.get("name", "Untitled"))

    def _generate_page_qml(self, page_node: dict[str, Any], file_name: str) -> str:
        """Generate QML for a page node."""
        imports = self.create_sailfish_imports()

        # Find frames on the page (usually these are screens)
        frames = [
            child
            for child in page_node.get("children", [])
            if child.get("type") == "FRAME"
        ]

        if not frames:
            return self._generate_simple_page(page_node.get("name", file_name), imports)

        # Generate QML for the first frame (main screen)
        main_frame = frames[0]
        page_name = self._safe_object_name(main_frame.get("name", "mainPage"))

        # Generate page header
        header_title = main_frame.get("name", "Main Page")

        # Generate children
        children_qml = self._generate_children_qml(
            main_frame.get("children", []),
            level=1,
            parent_bounds=main_frame.get("absoluteBoundingBox", {}),
        )

        # Create the complete page
        return f"""{imports}

Page {{
    objectName: "{page_name}"
    allowedOrientations: Orientation.All

    PageHeader {{
        id: pageHeader
        title: qsTr("{header_title}")
    }}

{children_qml}
}}"""

    def _generate_children_qml(
        self,
        children: list[dict[str, Any]],
        level: int = 1,
        parent_bounds: dict[str, Any] = None,
    ) -> str:
        """Generate QML for child nodes."""
        if not children:
            return ""

        qml_parts = []
        indent = "    " * level

        for child in children:
            child_qml = self._generate_node_qml(child, level, parent_bounds)
            if child_qml:
                qml_parts.append(f"{indent}{child_qml}")

        return "\n".join(qml_parts)

    def _generate_node_qml(
        self, node: dict[str, Any], level: int, parent_bounds: dict[str, Any] = None
    ) -> str:
        """Generate QML for a single node."""
        from aurora_mcp.utils.component_mapper import map_figma_node_to_qml

        mapped = map_figma_node_to_qml(node)
        qml_type = mapped["qml_type"]
        properties = mapped["properties"]

        # Generate basic properties
        props_lines = []

        # Object name for debugging
        safe_name = self._safe_object_name(node.get("name", "item"))
        props_lines.append(f'objectName: "{safe_name}"')

        # Size properties
        width = properties.get("width", 100)
        height = properties.get("height", 100)

        if width != 100:
            props_lines.append(f"width: {width}")
        if height != 100:
            props_lines.append(f"height: {height}")

        # Positioning (convert to relative if parent bounds available)
        x, y = self._calculate_relative_position(properties, parent_bounds)
        if x != 0:
            props_lines.append(f"x: {x}")
        if y != 0:
            props_lines.append(f"y: {y}")

        # Type-specific properties
        if qml_type == "Text" or qml_type == "Label":
            text_content = properties.get("text", "")
            if text_content:
                props_lines.append(
                    f'text: qsTr("{self._escape_qml_string(text_content)}")'
                )

            # Font size
            font_size = properties.get("font_size")
            if font_size:
                props_lines.append(f"font.pixelSize: {font_size}")

        elif qml_type == "Rectangle":
            # Color
            color = properties.get("color")
            if color:
                props_lines.append(f"color: {color}")

            # Border
            border_color = properties.get("border_color")
            border_width = properties.get("border_width", 0)
            if border_color and border_width > 0:
                props_lines.append(f"border.color: {border_color}")
                props_lines.append(f"border.width: {border_width}")

            # Corner radius
            radius = properties.get("radius", 0)
            if radius > 0:
                props_lines.append(f"radius: {radius}")

        # Opacity
        opacity = properties.get("opacity", 1.0)
        if opacity != 1.0:
            props_lines.append(f"opacity: {opacity}")

        # Interactive elements
        if mapped.get("is_interactive", False):
            props_lines.append("")  # Empty line for separation
            props_lines.append("MouseArea {")
            props_lines.append("    anchors.fill: parent")
            props_lines.append("    onClicked: {")
            props_lines.append("        // TODO: Add click handler")
            props_lines.append("    }")
            props_lines.append("}")

        # Handle children
        children = node.get("children", [])
        children_qml = ""
        if children:
            children_qml = "\n" + self._generate_children_qml(
                children, level + 1, node.get("absoluteBoundingBox", {})
            )

        # Assemble the QML
        if props_lines or children_qml:
            props_str = ""
            if props_lines:
                indent = "    "
                props_str = "\n" + "\n".join(f"{indent}{prop}" for prop in props_lines)

            return f"""{qml_type} {{{props_str}{children_qml}
}}"""
        else:
            return f"{qml_type} {{}}"

    def _calculate_relative_position(
        self, properties: dict[str, Any], parent_bounds: dict[str, Any] = None
    ) -> tuple[float, float]:
        """Calculate relative position within parent."""
        abs_x = properties.get("x", 0)
        abs_y = properties.get("y", 0)

        if not parent_bounds:
            return abs_x, abs_y

        parent_x = parent_bounds.get("x", 0)
        parent_y = parent_bounds.get("y", 0)

        return abs_x - parent_x, abs_y - parent_y

    def create_sailfish_imports(self) -> str:
        """Generate standard imports for Sailfish Silica."""
        return """import QtQuick 2.0
import Sailfish.Silica 1.0"""

    def _generate_empty_page(self) -> str:
        """Generate an empty page template."""
        imports = self.create_sailfish_imports()
        return f"""{imports}

Page {{
    objectName: "mainPage"
    allowedOrientations: Orientation.All

    PageHeader {{
        title: qsTr("Main Page")
    }}

    Label {{
        anchors.centerIn: parent
        text: qsTr("Generated from Figma")
        color: Theme.primaryColor
    }}
}}"""

    def _generate_simple_page(self, page_name: str, imports: str) -> str:
        """Generate a simple page with just a header."""
        safe_name = self._safe_object_name(page_name)
        return f"""{imports}

Page {{
    objectName: "{safe_name}"
    allowedOrientations: Orientation.All

    PageHeader {{
        title: qsTr("{page_name}")
    }}
}}"""

    def _safe_object_name(self, name: str) -> str:
        """Convert name to safe QML objectName."""
        import re

        # Remove special characters, replace spaces
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "", name.replace(" ", "_"))

        # Ensure it starts with a letter
        if not safe_name or safe_name[0].isdigit():
            safe_name = "item_" + safe_name

        # Make it camelCase
        parts = safe_name.split("_")
        if len(parts) > 1:
            safe_name = parts[0].lower() + "".join(
                word.capitalize() for word in parts[1:]
            )
        else:
            safe_name = safe_name.lower()

        return safe_name or "item"

    def _escape_qml_string(self, text: str) -> str:
        """Escape string for QML usage."""
        return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    def generate_component_file(
        self,
        component_name: str,
        figma_node: dict[str, Any],
        properties: list[str] = None,
    ) -> str:
        """
        Generate a reusable QML component file.

        Args:
            component_name: Name of the component
            figma_node: Figma node data
            properties: List of custom properties to expose

        Returns:
            QML component code
        """
        from aurora_mcp.utils.component_mapper import map_figma_node_to_qml

        imports = self.create_sailfish_imports()
        mapped = map_figma_node_to_qml(figma_node)
        base_type = mapped["qml_type"]

        # Generate property declarations
        property_declarations = []
        if properties:
            for prop in properties:
                property_declarations.append(f"property var {prop}")

        # Generate the component
        props_str = ""
        if property_declarations:
            props_str = "\n    " + "\n    ".join(property_declarations) + "\n"

        # Generate basic structure
        node_qml = self._generate_node_qml(figma_node, 1)

        return f"""{imports}

{base_type} {{{props_str}
    objectName: "{self._safe_object_name(component_name)}"

    // Component implementation
{self._indent_code(node_qml, 1)}
}}"""

    def generate_layout_from_auto_layout(self, node: dict[str, Any]) -> str:
        """Generate QML Layout from Figma auto-layout."""
        from aurora_mcp.utils.component_mapper import extract_auto_layout_info

        auto_layout = extract_auto_layout_info(node)
        if not auto_layout:
            return self._generate_node_qml(node, 0)

        layout_mode = auto_layout.get("layout_mode", "NONE")
        spacing = auto_layout.get("item_spacing", 0)

        if layout_mode == "HORIZONTAL":
            layout_type = "RowLayout"
        elif layout_mode == "VERTICAL":
            layout_type = "ColumnLayout"
        else:
            layout_type = "Item"

        # Generate children
        children_qml = self._generate_children_qml(
            node.get("children", []),
            level=1,
            parent_bounds=node.get("absoluteBoundingBox", {}),
        )

        props = []
        if spacing > 0:
            props.append(f"spacing: {spacing}")

        # Add padding
        padding_left = auto_layout.get("padding_left", 0)
        padding_right = auto_layout.get("padding_right", 0)
        padding_top = auto_layout.get("padding_top", 0)
        padding_bottom = auto_layout.get("padding_bottom", 0)

        if any([padding_left, padding_right, padding_top, padding_bottom]):
            props.append("anchors {")
            props.append("    fill: parent")
            if padding_left:
                props.append(f"    leftMargin: {padding_left}")
            if padding_right:
                props.append(f"    rightMargin: {padding_right}")
            if padding_top:
                props.append(f"    topMargin: {padding_top}")
            if padding_bottom:
                props.append(f"    bottomMargin: {padding_bottom}")
            props.append("}")

        props_str = ""
        if props:
            props_str = "\n    " + "\n    ".join(props) + "\n"

        return f"""{layout_type} {{{props_str}
{children_qml}
}}"""

    def _indent_code(self, code: str, level: int) -> str:
        """Add indentation to code block."""
        indent = "    " * level
        lines = code.split("\n")
        return "\n".join(indent + line if line.strip() else line for line in lines)

    def generate_app_main(self, app_name: str, main_page: str = "MainPage") -> str:
        """Generate main application QML file."""
        imports = self.create_sailfish_imports()

        return f"""{imports}

ApplicationWindow {{
    id: appWindow
    objectName: "applicationWindow"

    initialPage: Component {{ {main_page} {{}} }}

    cover: Qt.resolvedUrl("cover/CoverPage.qml")

    allowedOrientations: defaultAllowedOrientations
}}"""

    def generate_file_structure_info(
        self, figma_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze Figma data and suggest QML file structure.

        Args:
            figma_data: Processed Figma file data

        Returns:
            Suggested file structure information
        """
        document = figma_data.get("document", {})
        pages = document.get("children", [])

        structure = {
            "main_file": "Main.qml",
            "pages": [],
            "components": [],
            "suggested_structure": {},
        }

        for page in pages:
            page_name = page.get("name", "Untitled")
            safe_name = self._safe_object_name(page_name) + "Page"

            page_info = {
                "name": safe_name,
                "original_name": page_name,
                "file_path": f"qml/pages/{safe_name}.qml",
            }

            # Analyze frames in the page
            frames = [
                child
                for child in page.get("children", [])
                if child.get("type") == "FRAME"
            ]

            for frame in frames:
                frame_info = self._analyze_frame_for_components(frame)
                if frame_info["reusable_components"]:
                    page_info["components"] = frame_info["reusable_components"]

            structure["pages"].append(page_info)

        # Suggest directory structure
        structure["suggested_structure"] = {
            "qml/": {
                "pages/": [f"{page['name']}.qml" for page in structure["pages"]],
                "components/": ["CustomButton.qml", "ListItem.qml"],
                "cover/": ["CoverPage.qml"],
            },
            "assets/": {"images/": [], "icons/": []},
        }

        return structure

    def _analyze_frame_for_components(self, frame: dict[str, Any]) -> dict[str, Any]:
        """Analyze frame to identify reusable components."""
        analysis = {
            "total_elements": 0,
            "reusable_components": [],
            "layout_type": "freeform",
        }

        children = frame.get("children", [])
        analysis["total_elements"] = len(children)

        # Look for repeated patterns
        element_patterns = {}
        for child in children:
            element_type = child.get("type", "UNKNOWN")
            element_name = child.get("name", "").lower()

            # Simple pattern detection
            pattern_key = f"{element_type}_{element_name}"
            if pattern_key not in element_patterns:
                element_patterns[pattern_key] = []
            element_patterns[pattern_key].append(child)

        # Identify reusable components
        for pattern, elements in element_patterns.items():
            if len(elements) > 1:  # Repeated pattern
                component_name = self._suggest_component_name(elements[0])
                analysis["reusable_components"].append(
                    {
                        "name": component_name,
                        "count": len(elements),
                        "type": elements[0].get("type", "UNKNOWN"),
                        "base_element": elements[0],
                    }
                )

        return analysis

    def _suggest_component_name(self, element: dict[str, Any]) -> str:
        """Suggest a component name based on element properties."""
        element_name = element.get("name", "").lower()
        element_type = element.get("type", "").lower()

        # Common component name patterns
        if "button" in element_name or "btn" in element_name:
            return "CustomButton"
        elif "card" in element_name:
            return "InfoCard"
        elif "item" in element_name or "list" in element_name:
            return "ListItem"
        elif "header" in element_name:
            return "SectionHeader"
        elif element_type == "text":
            return "CustomLabel"
        else:
            safe_name = self._safe_object_name(element_name or "custom")
            return safe_name.capitalize() + "Component"
