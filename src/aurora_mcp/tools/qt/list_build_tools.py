from typing import Any
from pathlib import Path
import os

from fastmcp import Context
from aurora_mcp.decorators import DevelopmentStatus, development_status



async def list_build_tools(ctx: Context) -> dict[str, Any]:
    """List available build tools and their status."""
    try:
        aurora_home = Path(os.getenv("AURORA_HOME", "~/AuroraOS"))
        tools_status = {"tools": []}

        # Check SFDK
        sfdk_available = (aurora_home / "sfdk").exists()
        sfdk_info = {
            "name": "SFDK (Sailfish SDK)",
            "type": "sfdk",
            "available": sfdk_available,
            "description": "Modern build system using build engine containers",
        }

        if sfdk_available:
            sfdk_info["path"] = str(aurora_home / "sfdk")
            try:
                from aurora_mcp.utils.sfdk_wrapper import SFDKWrapper
                sfdk = SFDKWrapper(aurora_home)
                if sfdk.is_available():
                    version_info = await sfdk.get_version()
                    sfdk_info["version"] = version_info.get("version")
            except Exception as e:
                sfdk_info["error"] = f"Failed to get version: {str(e)}"

        tools_status["tools"].append(sfdk_info)

        # Check PSDK
        psdk_path = aurora_home / "psdk"
        psdk_info = {
            "name": "PSDK (Platform SDK)",
            "type": "psdk",
            "available": psdk_path.exists(),
            "description": "Traditional chroot-based build environment",
        }

        if psdk_path.exists():
            psdk_info["path"] = str(psdk_path)
            # Check for common PSDK tools
            psdk_tools = []
            for tool in ["sb2", "qmake", "cmake"]:
                tool_path = psdk_path / "bin" / tool
                if tool_path.exists():
                    psdk_tools.append(tool)
            psdk_info["available_tools"] = psdk_tools
        else:
            psdk_info["note"] = f"PSDK not found at {psdk_path}"

        tools_status["tools"].append(psdk_info)

        # Recommendations
        available_tools = [tool for tool in tools_status["tools"] if tool["available"]]

        if not available_tools:
            tools_status["recommendation"] = "Install Aurora OS SDK (SFDK recommended)"
            tools_status["status"] = "no_tools"
        elif len(available_tools) == 1:
            tools_status["recommendation"] = f"Using {available_tools[0]['name']}"
            tools_status["status"] = "single_tool"
        else:
            tools_status["recommendation"] = "Multiple tools available, SFDK recommended for new projects"
            tools_status["status"] = "multiple_tools"

        return tools_status

    except Exception as e:
        return {"error": f"Failed to list build tools: {str(e)}"}