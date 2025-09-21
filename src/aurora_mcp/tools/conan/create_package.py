from typing import Any
from pathlib import Path

from fastmcp import Context
from aurora_mcp.decorators import DevelopmentStatus, development_status



async def create_conan_package(
    ctx: Context, recipe_path: str, package_reference: str
) -> dict[str, Any]:
    """Create Conan package.

    Args:
        recipe_path: Path to conanfile.py
        package_reference: Package reference
    """
    try:
        recipe = Path(recipe_path)
        if not recipe.exists():
            return {"error": f"Recipe file {recipe_path} does not exist"}

        if not recipe.name == "conanfile.py":
            return {"error": f"Invalid recipe file: {recipe_path}. Expected conanfile.py"}

        conan_command = ["conan", "create", str(recipe.parent), package_reference]

        return {
            "status": "success",
            "message": f"Creating Conan package from {recipe_path}",
            "recipe_path": recipe_path,
            "package_reference": package_reference,
            "conan_command": " ".join(conan_command),
        }

    except Exception as e:
        return {"error": f"Conan package creation failed: {str(e)}"}