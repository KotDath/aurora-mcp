"""Component mapper for converting Figma nodes to QML components."""

from enum import Enum
from typing import Any


class FigmaNodeType(Enum):
    """Enumeration of Figma node types."""

    DOCUMENT = "DOCUMENT"
    CANVAS = "CANVAS"
    FRAME = "FRAME"
    GROUP = "GROUP"
    VECTOR = "VECTOR"
    BOOLEAN_OPERATION = "BOOLEAN_OPERATION"
    STAR = "STAR"
    LINE = "LINE"
    ELLIPSE = "ELLIPSE"
    REGULAR_POLYGON = "REGULAR_POLYGON"
    RECTANGLE = "RECTANGLE"
    TEXT = "TEXT"
    SLICE = "SLICE"
    COMPONENT = "COMPONENT"
    COMPONENT_SET = "COMPONENT_SET"
    INSTANCE = "INSTANCE"


# Mapping from Figma node types to possible QML component types
FIGMA_TO_QML_MAPPING = {
    FigmaNodeType.FRAME: ["Page", "Item", "Rectangle"],
    FigmaNodeType.TEXT: ["Label", "Text"],
    FigmaNodeType.RECTANGLE: ["Rectangle"],
    FigmaNodeType.ELLIPSE: ["Rectangle"],  # с radius для круглых углов
    FigmaNodeType.GROUP: ["Item"],
    FigmaNodeType.INSTANCE: ["Component"],
    FigmaNodeType.COMPONENT: ["Component"],
    FigmaNodeType.VECTOR: ["Canvas", "Item"],  # Для SVG-подобных элементов
    FigmaNodeType.LINE: ["Rectangle"],  # Тонкий прямоугольник
    FigmaNodeType.STAR: ["Canvas", "Item"],
    FigmaNodeType.REGULAR_POLYGON: ["Canvas", "Item"],
}

# Sailfish Silica component suggestions based on common patterns
SAILFISH_COMPONENT_PATTERNS = {
    "button": "Button",
    "list": "SilicaListView",
    "header": "PageHeader",
    "menu": "PullDownMenu",
    "text_field": "TextField",
    "text_area": "TextArea",
    "page": "Page",
    "dialog": "Dialog",
    "switch": "TextSwitch",
    "slider": "Slider",
    "progress": "ProgressBar",
    "icon": "IconButton",
}


def map_figma_node_to_qml(node: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Figma node to QML component information.

    Args:
        node: Figma node data

    Returns:
        Dictionary containing QML component information
    """
    node_type_str = node.get("type", "FRAME")

    try:
        node_type = FigmaNodeType(node_type_str)
    except ValueError:
        # Unknown node type, default to Item
        node_type = FigmaNodeType.FRAME

    qml_options = FIGMA_TO_QML_MAPPING.get(node_type, ["Item"])
    qml_type = choose_best_qml_type(node, qml_options)

    return {
        "qml_type": qml_type,
        "figma_type": node_type_str,
        "name": node.get("name", "untitled"),
        "properties": extract_qml_properties(node),
        "children": node.get("children", []),
        "constraints": node.get("constraints", {}),
        "effects": node.get("effects", []),
        "fills": node.get("fills", []),
        "strokes": node.get("strokes", []),
        "auto_layout": extract_auto_layout_info(node),
        "is_interactive": detect_interactive_element(node),
        "sailfish_suggestion": suggest_sailfish_component(node),
    }


def choose_best_qml_type(node: dict[str, Any], options: list[str]) -> str:
    """
    Choose the most appropriate QML type based on node properties.

    Args:
        node: Figma node data
        options: List of possible QML types

    Returns:
        Best QML type for this node
    """
    if len(options) == 1:
        return options[0]

    node_name = node.get("name", "").lower()

    # Check for Page indicators
    if "Page" in options:
        page_indicators = ["page", "screen", "view", "main", "home"]
        if any(indicator in node_name for indicator in page_indicators):
            return "Page"

    # Check for Rectangle vs Item
    if "Rectangle" in options and "Item" in options:
        # Use Rectangle if has visible fills or strokes
        fills = node.get("fills", [])
        strokes = node.get("strokes", [])

        has_visible_fill = any(fill.get("visible", True) for fill in fills)
        has_visible_stroke = any(stroke.get("visible", True) for stroke in strokes)

        if has_visible_fill or has_visible_stroke:
            return "Rectangle"
        else:
            return "Item"

    # Check for interactive elements
    if detect_interactive_element(node):
        interactive_options = [
            opt for opt in options if opt in ["Button", "IconButton"]
        ]
        if interactive_options:
            return interactive_options[0]

    # Default to first option
    return options[0]


def extract_qml_properties(node: dict[str, Any]) -> dict[str, Any]:
    """
    Extract QML properties from Figma node.

    Args:
        node: Figma node data

    Returns:
        Dictionary of QML properties
    """
    absolute_bounding_box = node.get("absoluteBoundingBox", {})

    properties = {
        "x": absolute_bounding_box.get("x", 0),
        "y": absolute_bounding_box.get("y", 0),
        "width": absolute_bounding_box.get("width", 100),
        "height": absolute_bounding_box.get("height", 100),
        "opacity": node.get("opacity", 1.0),
        "visible": node.get("visible", True),
        "rotation": node.get("rotation", 0),
    }

    # Add text-specific properties
    if node.get("type") == "TEXT":
        properties.update(extract_text_properties(node))

    # Add fill colors
    fill_colors = extract_fill_colors(node)
    if fill_colors:
        properties["color"] = fill_colors[0]  # Use first color

    # Add stroke properties
    stroke_colors = extract_stroke_colors(node)
    stroke_weight = node.get("strokeWeight", 0)
    if stroke_colors and stroke_weight > 0:
        properties["border_color"] = stroke_colors[0]
        properties["border_width"] = stroke_weight

    # Add corner radius for rectangles
    if node.get("type") == "RECTANGLE":
        corner_radius = node.get("cornerRadius", 0)
        if corner_radius > 0:
            properties["radius"] = corner_radius

    return properties


def extract_text_properties(node: dict[str, Any]) -> dict[str, Any]:
    """Extract text-specific properties from TEXT node."""
    properties = {}

    # Text content
    text_content = node.get("characters", "")
    if text_content:
        properties["text"] = text_content

    # Font properties
    style = node.get("style", {})
    if style:
        if "fontFamily" in style:
            properties["font_family"] = style["fontFamily"]
        if "fontSize" in style:
            properties["font_size"] = style["fontSize"]
        if "fontWeight" in style:
            properties["font_weight"] = style["fontWeight"]
        if "textAlignHorizontal" in style:
            alignment_map = {
                "LEFT": "Text.AlignLeft",
                "CENTER": "Text.AlignHCenter",
                "RIGHT": "Text.AlignRight",
                "JUSTIFIED": "Text.AlignJustify",
            }
            properties["horizontal_alignment"] = alignment_map.get(
                style["textAlignHorizontal"], "Text.AlignLeft"
            )

    return properties


def extract_fill_colors(node: dict[str, Any]) -> list[str]:
    """Extract fill colors from node in QML-compatible format."""
    colors = []
    fills = node.get("fills", [])

    for fill in fills:
        if fill.get("type") == "SOLID" and fill.get("visible", True):
            color = fill.get("color", {})
            r = int(color.get("r", 0) * 255)
            g = int(color.get("g", 0) * 255)
            b = int(color.get("b", 0) * 255)
            a = color.get("a", 1.0)

            if a < 1.0:
                colors.append(
                    f"Qt.rgba({r / 255:.3f}, {g / 255:.3f}, {b / 255:.3f}, {a:.3f})"
                )
            else:
                colors.append(f'"#{r:02x}{g:02x}{b:02x}"')

    return colors


def extract_stroke_colors(node: dict[str, Any]) -> list[str]:
    """Extract stroke colors from node in QML-compatible format."""
    colors = []
    strokes = node.get("strokes", [])

    for stroke in strokes:
        if stroke.get("type") == "SOLID" and stroke.get("visible", True):
            color = stroke.get("color", {})
            r = int(color.get("r", 0) * 255)
            g = int(color.get("g", 0) * 255)
            b = int(color.get("b", 0) * 255)
            a = color.get("a", 1.0)

            if a < 1.0:
                colors.append(
                    f"Qt.rgba({r / 255:.3f}, {g / 255:.3f}, {b / 255:.3f}, {a:.3f})"
                )
            else:
                colors.append(f'"#{r:02x}{g:02x}{b:02x}"')

    return colors


def extract_auto_layout_info(node: dict[str, Any]) -> dict[str, Any]:
    """Extract auto layout information if present."""
    if "layoutMode" not in node or node.get("layoutMode") == "NONE":
        return {}

    return {
        "layout_mode": node.get("layoutMode", "NONE"),
        "primary_axis_sizing_mode": node.get("primaryAxisSizingMode", "AUTO"),
        "counter_axis_sizing_mode": node.get("counterAxisSizingMode", "AUTO"),
        "primary_axis_align_items": node.get("primaryAxisAlignItems", "MIN"),
        "counter_axis_align_items": node.get("counterAxisAlignItems", "MIN"),
        "padding_left": node.get("paddingLeft", 0),
        "padding_right": node.get("paddingRight", 0),
        "padding_top": node.get("paddingTop", 0),
        "padding_bottom": node.get("paddingBottom", 0),
        "item_spacing": node.get("itemSpacing", 0),
        "layout_wrap": node.get("layoutWrap", "NO_WRAP"),
    }


def detect_interactive_element(node: dict[str, Any]) -> bool:
    """
    Detect if a node represents an interactive element.

    Args:
        node: Figma node data

    Returns:
        True if node appears to be interactive
    """
    node_name = node.get("name", "").lower()

    # Check for interactive keywords in name
    interactive_keywords = [
        "button",
        "btn",
        "click",
        "tap",
        "press",
        "link",
        "menu",
        "item",
        "input",
        "field",
        "switch",
        "toggle",
        "slider",
        "checkbox",
        "radio",
    ]

    if any(keyword in node_name for keyword in interactive_keywords):
        return True

    # Check for component instances (often interactive)
    if node.get("type") in ["COMPONENT", "INSTANCE"]:
        return True

    # Check if has mouse/touch interactions in Figma
    # (This would require additional Figma data about interactions)

    return False


def suggest_sailfish_component(node: dict[str, Any]) -> str | None:
    """
    Suggest appropriate Sailfish Silica component based on node characteristics.

    Args:
        node: Figma node data

    Returns:
        Suggested Sailfish component name or None
    """
    node_name = node.get("name", "").lower()

    # Match against Sailfish patterns
    for pattern, component in SAILFISH_COMPONENT_PATTERNS.items():
        if pattern in node_name:
            return component

    # Special cases based on structure
    if node.get("type") == "TEXT":
        # Check if it's likely an input field
        if any(keyword in node_name for keyword in ["input", "field", "enter", "type"]):
            if "area" in node_name or "multi" in node_name:
                return "TextArea"
            else:
                return "TextField"
        else:
            return "Label"

    # Check for list-like structures
    children = node.get("children", [])
    if len(children) > 3:
        # Multiple similar children might be a list
        return "SilicaListView"

    return None


def analyze_layout_structure(node: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze the layout structure of a node and its children.

    Args:
        node: Figma node data

    Returns:
        Layout analysis information
    """
    children = node.get("children", [])
    if not children:
        return {"type": "leaf", "children_count": 0}

    # Analyze auto layout
    auto_layout = extract_auto_layout_info(node)
    if auto_layout:
        layout_mode = auto_layout.get("layout_mode", "NONE")
        if layout_mode == "HORIZONTAL":
            return {
                "type": "horizontal_layout",
                "children_count": len(children),
                "suggested_qml": "RowLayout",
                "spacing": auto_layout.get("item_spacing", 0),
            }
        elif layout_mode == "VERTICAL":
            return {
                "type": "vertical_layout",
                "children_count": len(children),
                "suggested_qml": "ColumnLayout",
                "spacing": auto_layout.get("item_spacing", 0),
            }

    # Analyze manual positioning
    return analyze_manual_layout(children)


def analyze_manual_layout(children: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze manually positioned children to suggest layout type."""
    if len(children) < 2:
        return {"type": "single_child", "children_count": len(children)}

    # Get positions of children
    positions = []
    for child in children:
        bounds = child.get("absoluteBoundingBox", {})
        positions.append(
            {
                "x": bounds.get("x", 0),
                "y": bounds.get("y", 0),
                "width": bounds.get("width", 0),
                "height": bounds.get("height", 0),
            }
        )

    # Check if children are arranged horizontally
    y_positions = [pos["y"] for pos in positions]
    if max(y_positions) - min(y_positions) < 50:  # Similar Y positions
        return {
            "type": "horizontal_manual",
            "children_count": len(children),
            "suggested_qml": "Row",
        }

    # Check if children are arranged vertically
    x_positions = [pos["x"] for pos in positions]
    if max(x_positions) - min(x_positions) < 50:  # Similar X positions
        return {
            "type": "vertical_manual",
            "children_count": len(children),
            "suggested_qml": "Column",
        }

    # Check for grid-like arrangement
    unique_x = len(set(round(x / 50) * 50 for x in x_positions))  # Group by 50px
    unique_y = len(set(round(y / 50) * 50 for y in y_positions))

    if unique_x > 1 and unique_y > 1:
        return {
            "type": "grid_manual",
            "children_count": len(children),
            "suggested_qml": "Grid",
            "columns": unique_x,
            "rows": unique_y,
        }

    return {
        "type": "freeform",
        "children_count": len(children),
        "suggested_qml": "Item",
    }


def get_component_usage_priority() -> list[str]:
    """
    Get prioritized list of QML components for Sailfish apps.

    Returns:
        List of component names in order of preference
    """
    return [
        # Sailfish Silica components (preferred)
        "Page",
        "PageHeader",
        "SilicaListView",
        "SilicaFlickable",
        "Label",
        "Button",
        "IconButton",
        "TextField",
        "TextArea",
        "PullDownMenu",
        "PushUpMenu",
        "MenuItem",
        "TextSwitch",
        "Slider",
        "ProgressBar",
        "BusyIndicator",
        # Standard QML components (fallback)
        "Item",
        "Rectangle",
        "Text",
        "Image",
        "RowLayout",
        "ColumnLayout",
        "GridLayout",
        "Row",
        "Column",
        "Grid",
        "Flickable",
        "ScrollView",
    ]
