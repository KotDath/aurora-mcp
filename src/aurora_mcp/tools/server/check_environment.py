from typing import Any
from pathlib import Path
import os
import shutil

from fastmcp import Context
from aurora_mcp.decorators import DevelopmentStatus, development_status



async def check_aurora_environment(ctx: Context) -> dict[str, Any]:
    """Check Aurora OS development environment status."""
    try:
        aurora_home = Path(os.getenv("AURORA_HOME", "~/AuroraOS"))

        status = {
            "aurora_home": str(aurora_home),
            "aurora_home_exists": aurora_home.exists(),
            "psdk_available": (aurora_home / "psdk").exists(),
            "build_engine_available": (aurora_home / "build-engine").exists(),
            "projects_dir": (aurora_home / "projects").exists(),
        }

        # Check for Aurora CLI
        try:
            status["aurora_cli"] = shutil.which("aurora-cli") is not None
        except Exception:
            status["aurora_cli"] = False

        # Check SFDK
        status["sfdk_available"] = (aurora_home / "sfdk").exists()
        if status["sfdk_available"]:
            try:
                from aurora_mcp.utils.sfdk_wrapper import SFDKWrapper
                sfdk = SFDKWrapper(aurora_home)
                if sfdk.is_available():
                    version_info = await sfdk.get_version()
                    status["sfdk_version"] = version_info.get("version")
            except Exception as e:
                status["sfdk_error"] = str(e)

        # Overall status
        essential_tools = [
            status["psdk_available"],
            status["sfdk_available"],
        ]

        if any(essential_tools):
            status["overall_status"] = "ready"
        elif status["aurora_home_exists"]:
            status["overall_status"] = "partial"
        else:
            status["overall_status"] = "not_setup"

        # Recommendations
        recommendations = []
        if not any(essential_tools):
            recommendations.append("Install Aurora OS SDK (PSDK or SFDK)")
        if not status["aurora_home_exists"]:
            recommendations.append(f"Create Aurora home directory at {aurora_home}")

        status["recommendations"] = recommendations

        return status

    except Exception as e:
        return {"error": f"Failed to check environment: {str(e)}"}