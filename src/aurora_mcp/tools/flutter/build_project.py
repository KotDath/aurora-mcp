import os
import subprocess
from pathlib import Path
from typing import Any

from fastmcp import Context


async def build_flutter_project(
    ctx: Context, project_path: str, target_arch: str = "armv7hl"
) -> dict[str, Any]:
    """Build Flutter project for Aurora OS.

    Args:
        project_path: Path to Flutter project
        target_arch: Target architecture
    """
    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": f"Project directory {project_path} does not exist"}

        # Check if it's a Flutter project
        pubspec_file = project_dir / "pubspec.yaml"
        if not pubspec_file.exists():
            return {"error": "Not a Flutter project (pubspec.yaml not found)"}

        aurora_home = Path(os.getenv("AURORA_HOME", "~/AuroraOS"))

        # Check for Flutter SDK
        flutter_sdk = aurora_home / "flutter"
        if not flutter_sdk.exists():
            # Try to find flutter in PATH
            try:
                flutter_path = subprocess.run(
                    ["which", "flutter"], capture_output=True, text=True, check=True
                ).stdout.strip()
            except subprocess.CalledProcessError:
                return {"error": "Flutter SDK not found"}
        else:
            flutter_path = str(flutter_sdk / "bin" / "flutter")

        result = {
            "status": "success",
            "message": f"Building Flutter project at {project_path}",
            "project_path": project_path,
            "target_arch": target_arch,
            "flutter_path": flutter_path,
            "aurora_home": str(aurora_home),
        }

        # Basic Flutter build commands
        build_commands = [
            f"{flutter_path} clean",
            f"{flutter_path} pub get",
            f"{flutter_path} build aurora --target-platform aurora-{target_arch}",
        ]

        result["build_commands"] = build_commands
        result["build_dir"] = str(project_dir / "build" / "aurora" / target_arch)

        return result

    except Exception as e:
        return {"error": f"Flutter build failed: {str(e)}"}
