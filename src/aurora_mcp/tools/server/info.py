from typing import Any
from pathlib import Path
import os

from fastmcp import Context
from aurora_mcp.decorators import DevelopmentStatus, development_status



async def aurora_mcp_info(ctx: Context) -> dict[str, Any]:
    """Get Aurora MCP server information."""
    try:
        aurora_home = Path(os.getenv("AURORA_HOME", "~/AuroraOS"))

        return {
            "server": "Aurora MCP",
            "version": "0.1.0",
            "aurora_home": str(aurora_home),
            "available_tools": [
                "Qt Build Tools",
                "Flutter Build Tools",
                "RPM Packaging Tools",
                "Template Management Tools",
                "Conan Integration Tools",
            ],
            "supported_architectures": ["armv7hl", "aarch64", "x86_64"],
            "tool_categories": {
                "qt": ["build_qt_project", "configure_qt_environment", "list_qt_targets", "list_build_tools"],
                "flutter": ["build_flutter_project", "setup_flutter_embedder"],
                "rpm": ["create_rpm_package", "sign_rpm_package", "validate_rpm_package"],
                "template": ["create_project_from_template", "list_available_templates"],
                "conan": ["install_conan_dependencies", "create_conan_package"],
                "server": ["aurora_mcp_info", "check_aurora_environment"],
            }
        }

    except Exception as e:
        return {"error": f"Failed to get server info: {str(e)}"}