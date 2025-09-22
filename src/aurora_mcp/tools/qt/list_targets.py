import os
from pathlib import Path
from typing import Any

from fastmcp import Context


async def list_qt_targets(ctx: Context) -> dict[str, Any]:
    """List available Qt build targets."""
    try:
        aurora_home = Path(os.getenv("AURORA_HOME", "~/AuroraOS"))

        targets = {
            "sfdk_available": (aurora_home / "sfdk").exists(),
            "psdk_available": (aurora_home / "psdk").exists(),
            "targets": [],
        }

        # Check SFDK targets
        if targets["sfdk_available"]:
            try:
                from aurora_mcp.utils.sfdk_wrapper import SFDKWrapper

                sfdk = SFDKWrapper(aurora_home)
                if sfdk.is_available():
                    sfdk_targets = await sfdk.list_targets()
                    targets["targets"].extend(sfdk_targets.get("targets", []))
            except Exception as e:
                targets["sfdk_error"] = str(e)
                # Fallback to standard targets
                targets["targets"].extend(
                    [
                        {"name": "SailfishOS-4.5.0.19-armv7hl", "arch": "armv7hl"},
                        {"name": "SailfishOS-4.5.0.19-aarch64", "arch": "aarch64"},
                        {"name": "SailfishOS-4.5.0.19-i486", "arch": "i486"},
                    ]
                )

        # Add PSDK targets if available
        if targets["psdk_available"]:
            targets["psdk_targets"] = [
                {"name": "armv7hl", "description": "32-bit ARM architecture"},
                {"name": "aarch64", "description": "64-bit ARM architecture"},
                {
                    "name": "x86_64",
                    "description": "64-bit x86 architecture (for emulator)",
                },
            ]

        return targets

    except Exception as e:
        return {"error": f"Failed to list targets: {str(e)}"}
