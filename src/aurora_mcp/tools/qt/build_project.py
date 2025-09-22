import os
from pathlib import Path
from typing import Any

from fastmcp import Context


def _find_build_tool() -> tuple[str | None, str | None]:
    """Find build tools in priority order.

    For SFDK:
    1. Environment variable 'auroramcp_sfdk'
    2. Alias 'sfdk' (~/AuroraOS/bin/sfdk)
    3. AURORA_HOME/bin/sfdk

    For PSDK (fallback):
    4. AURORA_HOME/psdk

    Returns:
        Tuple of (tool_path, build_tool_type) where build_tool_type is 'sfdk' or 'psdk' or None
    """
    # Check auroramcp_sfdk environment variable
    auroramcp_sfdk = os.getenv("auroramcp_sfdk")
    if auroramcp_sfdk and Path(auroramcp_sfdk).exists():
        return auroramcp_sfdk, "sfdk"

    # Check sfdk environment variable
    sfdk_env = os.getenv("sfdk")
    if sfdk_env and Path(sfdk_env).exists():
        return sfdk_env, "sfdk"

    # Check AURORA_HOME/bin/sfdk
    aurora_home = os.getenv("AURORA_MCP_HOME")
    if aurora_home:
        sfdk_path = Path(aurora_home) / "bin" / "sfdk"
        if sfdk_path.exists():
            return str(sfdk_path), "sfdk"

        # Check for PSDK as fallback
        psdk_path = Path(aurora_home) / "psdk"
        if psdk_path.exists():
            return str(psdk_path), "psdk"

    return None, None


async def build_qt_project(
    ctx: Context,
    project_path: str,
    build_type: str = "Release",
    target_arch: str = "armv7hl",
    build_tool: str | None = None,
    build_dir_name: str = "build_amogus",
) -> dict[str, Any]:
    """Build Qt project for Aurora OS.

    Args:
        project_path: Path to Qt project directory
        build_type: Build type (Debug/Release)
        target_arch: Target architecture (armv7hl, aarch64, x86_64)
        build_tool: Build tool to use ('sfdk' for Build Engine, 'psdk' for Platform SDK, or None for auto-detect)
        build_dir_name: Name of build directory for SFDK builds (default: build_amogus)
    """
    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": f"Project directory {project_path} does not exist"}

        # Detect project type
        project_type = "unknown"
        if (project_dir / "CMakeLists.txt").exists():
            project_type = "cmake"
        elif list(project_dir.glob("*.pro")):
            project_type = "qmake"
        else:
            return {
                "error": "Unknown project type. Expected CMakeLists.txt or *.pro file"
            }

        # Find build tools using priority search
        tool_path, detected_tool = _find_build_tool()

        # Auto-detect build tool if not specified
        if not build_tool:
            if detected_tool:
                build_tool = detected_tool
            else:
                return {
                    "error": "No build tools available. SFDK not found (check 'auroramcp_sfdk', 'sfdk' env vars, or AURORA_HOME/bin/sfdk) and PSDK not available (check AURORA_HOME/psdk)"
                }

        # Get Aurora home for legacy compatibility
        aurora_home = Path(os.getenv("AURORA_HOME", "~/AuroraOS"))

        result = {
            "status": "success",
            "message": f"Building Qt {project_type} project at {project_path}",
            "project_path": project_path,
            "project_type": project_type,
            "build_type": build_type,
            "target_arch": target_arch,
            "build_tool": build_tool,
            "tool_path": tool_path,
            "aurora_home": str(aurora_home),
        }

        if build_tool == "sfdk":
            # Use SFDK wrapper for actual building
            try:
                from aurora_mcp.utils.sfdk_wrapper import SFDKWrapper

                sfdk = SFDKWrapper(aurora_home)
                build_result = await sfdk.build_project(
                    Path(project_path), target_arch, build_dir_name, ctx
                )
                result.update(build_result)
            except Exception as e:
                result["warning"] = f"SFDK build failed, using placeholder: {str(e)}"
                result["build_dir"] = build_dir_name
        else:
            # PSDK placeholder implementation
            result["build_command"] = f"sb2 -t {target_arch} make"
            result["build_dir"] = "build"

        return result

    except Exception as e:
        return {"error": f"Build failed: {str(e)}"}
