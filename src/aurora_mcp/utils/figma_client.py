"""Figma API client for fetching design data."""

import re
from typing import Any


class FigmaClient:
    """Client for interacting with Figma REST API."""

    def __init__(self, access_token: str):
        """
        Initialize Figma client with access token.

        Args:
            access_token: Personal Access Token for Figma API
        """
        self.access_token = access_token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": access_token,
            "Content-Type": "application/json",
        }

    def fetch_file(self, file_key: str) -> dict[str, Any]:
        """
        Fetch complete Figma file data.

        Args:
            file_key: Figma file key extracted from URL

        Returns:
            Complete file data including document tree

        Raises:
            requests.RequestException: If API request fails
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests library is required. Install with: pip install requests"
            )

        url = f"{self.base_url}/files/{file_key}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Figma file {file_key}: {str(e)}")

    def fetch_file_nodes(self, file_key: str, node_ids: list[str]) -> dict[str, Any]:
        """
        Fetch specific nodes from Figma file.

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to fetch

        Returns:
            Node data for specified nodes
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests library is required. Install with: pip install requests"
            )

        url = f"{self.base_url}/files/{file_key}/nodes"
        params = {"ids": ",".join(node_ids)}

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Figma nodes {node_ids}: {str(e)}")

    def extract_all_metadata(self, file_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract comprehensive metadata from Figma file data.

        Args:
            file_data: Raw Figma file data from API

        Returns:
            Structured metadata including all design information
        """
        return {
            "document": file_data.get("document", {}),
            "components": file_data.get("components", {}),
            "componentSets": file_data.get("componentSets", {}),
            "schemaVersion": file_data.get("schemaVersion", 0),
            "styles": file_data.get("styles", {}),
            "name": file_data.get("name", ""),
            "lastModified": file_data.get("lastModified", ""),
            "thumbnailUrl": file_data.get("thumbnailUrl", ""),
            "version": file_data.get("version", ""),
            "role": file_data.get("role", ""),
            "editorType": file_data.get("editorType", ""),
            "linkAccess": file_data.get("linkAccess", ""),
        }

    def get_file_images(
        self,
        file_key: str,
        node_ids: list[str],
        format: str = "png",
        scale: float = 1.0,
    ) -> dict[str, Any]:
        """
        Get image URLs for specified nodes.

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to get images for
            format: Image format (png, jpg, svg, pdf)
            scale: Image scale factor

        Returns:
            Dictionary mapping node IDs to image URLs
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests library is required. Install with: pip install requests"
            )

        url = f"{self.base_url}/images/{file_key}"
        params = {"ids": ",".join(node_ids), "format": format, "scale": scale}

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch images for nodes {node_ids}: {str(e)}")


def extract_file_key_from_url(figma_url: str) -> str:
    """
    Extract file key from Figma URL.

    Args:
        figma_url: Full Figma URL like https://www.figma.com/file/ABC123/title?node-id=1%3A2

    Returns:
        File key string

    Raises:
        ValueError: If URL doesn't contain valid file key
    """
    # Support different Figma URL formats:
    # https://www.figma.com/file/ABC123/title
    # https://www.figma.com/file/ABC123/title?node-id=1%3A2
    # https://www.figma.com/design/ABC123/title
    # https://figma.com/file/ABC123/title

    patterns = [
        r"/file/([a-zA-Z0-9]+)",
        r"/design/([a-zA-Z0-9]+)",
        r"figma\.com/(?:file|design)/([a-zA-Z0-9]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, figma_url)
        if match:
            return match.group(1)

    raise ValueError(
        f"Invalid Figma URL format: {figma_url}. Expected format: https://www.figma.com/file/FILE_KEY/title"
    )


def extract_node_id_from_url(figma_url: str) -> str | None:
    """
    Extract node ID from Figma URL if present.

    Args:
        figma_url: Figma URL that might contain node-id parameter

    Returns:
        Node ID string if found, None otherwise
    """
    # Look for node-id parameter in URL
    # ?node-id=1%3A2 (URL encoded) or ?node-id=1:2
    node_match = re.search(r"node-id=([^&]+)", figma_url)
    if node_match:
        node_id = node_match.group(1)
        # URL decode if needed
        import urllib.parse

        return urllib.parse.unquote(node_id)

    return None


def validate_figma_access_token(access_token: str) -> bool:
    """
    Validate Figma access token format.

    Args:
        access_token: Token to validate

    Returns:
        True if token format is valid
    """
    # Figma personal access tokens start with 'figd_' and are typically 73 characters
    if not access_token:
        return False

    if access_token.startswith("figd_") and len(access_token) >= 60:
        return True

    # Also accept older format tokens (for backward compatibility)
    if (
        len(access_token) >= 40
        and access_token.replace("-", "").replace("_", "").isalnum()
    ):
        return True

    return False


class FigmaDataExtractor:
    """Helper class for extracting specific data from Figma nodes."""

    @staticmethod
    def extract_text_content(node: dict[str, Any]) -> str | None:
        """Extract text content from text nodes."""
        if node.get("type") == "TEXT":
            return node.get("characters", "")
        return None

    @staticmethod
    def extract_fill_colors(node: dict[str, Any]) -> list[str]:
        """Extract fill colors from node."""
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
                    colors.append(f"rgba({r}, {g}, {b}, {a})")
                else:
                    colors.append(f"#{r:02x}{g:02x}{b:02x}")

        return colors

    @staticmethod
    def extract_stroke_colors(node: dict[str, Any]) -> list[str]:
        """Extract stroke colors from node."""
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
                    colors.append(f"rgba({r}, {g}, {b}, {a})")
                else:
                    colors.append(f"#{r:02x}{g:02x}{b:02x}")

        return colors

    @staticmethod
    def extract_bounds(node: dict[str, Any]) -> dict[str, float]:
        """Extract position and size information."""
        bounds = node.get("absoluteBoundingBox", {})
        return {
            "x": bounds.get("x", 0),
            "y": bounds.get("y", 0),
            "width": bounds.get("width", 0),
            "height": bounds.get("height", 0),
        }

    @staticmethod
    def extract_constraints(node: dict[str, Any]) -> dict[str, str]:
        """Extract layout constraints."""
        constraints = node.get("constraints", {})
        return {
            "horizontal": constraints.get("horizontal", "LEFT"),
            "vertical": constraints.get("vertical", "TOP"),
        }

    @staticmethod
    def extract_effects(node: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract visual effects (shadows, blur, etc.)."""
        return node.get("effects", [])

    @staticmethod
    def has_auto_layout(node: dict[str, Any]) -> bool:
        """Check if node uses auto layout."""
        return "layoutMode" in node and node.get("layoutMode") != "NONE"

    @staticmethod
    def extract_auto_layout_info(node: dict[str, Any]) -> dict[str, Any]:
        """Extract auto layout configuration."""
        if not FigmaDataExtractor.has_auto_layout(node):
            return {}

        return {
            "layoutMode": node.get("layoutMode", "NONE"),
            "primaryAxisSizingMode": node.get("primaryAxisSizingMode", "AUTO"),
            "counterAxisSizingMode": node.get("counterAxisSizingMode", "AUTO"),
            "primaryAxisAlignItems": node.get("primaryAxisAlignItems", "MIN"),
            "counterAxisAlignItems": node.get("counterAxisAlignItems", "MIN"),
            "paddingLeft": node.get("paddingLeft", 0),
            "paddingRight": node.get("paddingRight", 0),
            "paddingTop": node.get("paddingTop", 0),
            "paddingBottom": node.get("paddingBottom", 0),
            "itemSpacing": node.get("itemSpacing", 0),
            "layoutWrap": node.get("layoutWrap", "NO_WRAP"),
        }
