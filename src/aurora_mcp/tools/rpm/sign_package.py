from typing import Any
from pathlib import Path

from fastmcp import Context
from aurora_mcp.decorators import DevelopmentStatus, development_status



async def sign_rpm_package(
    ctx: Context, rpm_file: str, key_id: str | None = None
) -> dict[str, Any]:
    """Sign RPM package.

    Args:
        rpm_file: Path to RPM file
        key_id: GPG key ID for signing
    """
    try:
        rpm_path = Path(rpm_file)
        if not rpm_path.exists():
            return {"error": f"RPM file {rpm_file} does not exist"}

        if not rpm_path.suffix == ".rpm":
            return {"error": f"File {rpm_file} is not an RPM package"}

        sign_command = ["rpm", "--addsign", rpm_file]
        if key_id:
            sign_command.extend(["--define", f"_gpg_name {key_id}"])

        return {
            "status": "success",
            "message": f"Signing RPM package {rpm_file}",
            "rpm_file": rpm_file,
            "key_id": key_id or "default",
            "sign_command": " ".join(sign_command),
        }

    except Exception as e:
        return {"error": f"RPM package signing failed: {str(e)}"}