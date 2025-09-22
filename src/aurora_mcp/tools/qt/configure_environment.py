import os
from pathlib import Path
from typing import Any

from fastmcp import Context


async def configure_qt_environment(
    ctx: Context, target_arch: str = "armv7hl"
) -> dict[str, Any]:
    """Configure Qt build environment for Aurora OS.

    Args:
        target_arch: Target architecture
    """
    try:
        aurora_home = Path(os.getenv("AURORA_HOME", "~/AuroraOS"))

        # Check environment
        env_status = {
            "aurora_home": str(aurora_home),
            "aurora_home_exists": aurora_home.exists(),
            "target_arch": target_arch,
        }

        # Check PSDK
        psdk_path = aurora_home / "psdk"
        env_status["psdk_available"] = psdk_path.exists()

        if psdk_path.exists():
            env_status["psdk_path"] = str(psdk_path)
            # Check for Qt in PSDK
            qt_dirs = list(psdk_path.glob("**/qt*/include/QtCore"))
            if qt_dirs:
                env_status["qt_installed"] = True
                env_status["qt_path"] = str(qt_dirs[0].parent.parent)
                # Try to detect version
                for part in qt_dirs[0].parts:
                    if part.startswith("qt") and any(c.isdigit() for c in part):
                        env_status["qt_version"] = part
                        break
            else:
                env_status["qt_installed"] = False

        # Check SFDK
        env_status["sfdk_available"] = (aurora_home / "sfdk").exists()
        if env_status["sfdk_available"]:
            try:
                from aurora_mcp.utils.sfdk_wrapper import SFDKWrapper

                sfdk = SFDKWrapper(aurora_home)
                if sfdk.is_available():
                    version_info = await sfdk.get_version()
                    env_status["sfdk_version"] = version_info.get("version")
            except Exception as e:
                env_status["sfdk_error"] = str(e)

        # Recommendations
        recommendations = []
        if not env_status["psdk_available"] and not env_status["sfdk_available"]:
            recommendations.append("Install Aurora OS SDK (PSDK or SFDK)")
        elif env_status.get("qt_installed") is False:
            recommendations.append(f"Install Qt development packages for {target_arch}")

        env_status["recommendations"] = recommendations
        env_status["status"] = "ready" if not recommendations else "needs_setup"

        return env_status

    except Exception as e:
        return {"error": f"Failed to configure environment: {str(e)}"}
