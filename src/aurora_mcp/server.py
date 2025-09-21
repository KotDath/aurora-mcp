"""
Copyright 2025 Daniil Markevich (KotDath)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging

from aurora_mcp.tools import ALL_TOOLS

# Configure logging
configure_logging(
    level=logging.INFO,
    enable_rich_tracebacks=True,
)

logger = logging.getLogger(__name__)


def create_server(aurora_home: str | None = None) -> FastMCP:
    """Create Aurora MCP server with all tools registered.

    Args:
        aurora_home: Aurora OS home directory (default: ~/AuroraOS)

    Returns:
        FastMCP server instance with all tools registered
    """
    mcp = FastMCP("AuroraMCP")

    # Register all tools manually
    for tool_func in ALL_TOOLS:
        mcp.tool(tool_func)

    logger.info(f"Aurora MCP server created with {len(ALL_TOOLS)} tools")
    return mcp


# Legacy compatibility - keep existing AuroraMCP class
class AuroraMCP:
    """Legacy Aurora MCP Server class for backward compatibility."""

    def __init__(self, aurora_home: str | None = None):
        self.aurora_home = Path(aurora_home or "~/AuroraOS")
        self.mcp = create_server(aurora_home)

    def get_server(self) -> FastMCP:
        """Get the FastMCP server instance."""
        return self.mcp


# For direct usage
aurora_home = Path("~/AuroraOS")
server = create_server()