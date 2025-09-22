from pathlib import Path
from typing import Any

from fastmcp import Context


async def install_conan_dependencies(
    ctx: Context, conanfile_path: str, profile: str | None = None
) -> dict[str, Any]:
    """Install Conan dependencies.

    Args:
        conanfile_path: Path to conanfile.txt or conanfile.py
        profile: Conan profile to use
    """
    try:
        conanfile = Path(conanfile_path)
        if not conanfile.exists():
            return {"error": f"Conanfile {conanfile_path} does not exist"}

        if not (conanfile.name == "conanfile.txt" or conanfile.name == "conanfile.py"):
            return {
                "error": f"Invalid conanfile: {conanfile_path}. Expected conanfile.txt or conanfile.py"
            }

        conan_command = ["conan", "install", str(conanfile.parent)]
        if profile:
            conan_command.extend(["--profile", profile])

        return {
            "status": "success",
            "message": f"Installing Conan dependencies from {conanfile_path}",
            "conanfile_path": conanfile_path,
            "profile": profile or "default",
            "conan_command": " ".join(conan_command),
        }

    except Exception as e:
        return {"error": f"Conan dependencies installation failed: {str(e)}"}
