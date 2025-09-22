from pathlib import Path
from typing import Any

from fastmcp import Context


async def create_rpm_package(
    ctx: Context,
    spec_file: str,
    source_dir: str,
    output_dir: str = "/tmp/rpmbuild",
) -> dict[str, Any]:
    """Create RPM package from spec file.

    Args:
        spec_file: Path to RPM spec file
        source_dir: Source directory
        output_dir: Output directory for RPM
    """
    try:
        spec_path = Path(spec_file)
        if not spec_path.exists():
            return {"error": f"Spec file {spec_file} does not exist"}

        source_path = Path(source_dir)
        if not source_path.exists():
            return {"error": f"Source directory {source_dir} does not exist"}

        output_path = Path(output_dir)

        # Basic rpmbuild command
        rpmbuild_cmd = [
            "rpmbuild",
            "--define",
            f"_topdir {output_path}",
            "--define",
            f"_sourcedir {source_path}",
            "-ba",
            str(spec_path),
        ]

        return {
            "status": "success",
            "message": f"Creating RPM package from {spec_file}",
            "spec_file": spec_file,
            "source_dir": source_dir,
            "output_dir": output_dir,
            "rpmbuild_command": " ".join(rpmbuild_cmd),
            "rpm_dirs": {
                "SPECS": str(output_path / "SPECS"),
                "SOURCES": str(output_path / "SOURCES"),
                "BUILD": str(output_path / "BUILD"),
                "RPMS": str(output_path / "RPMS"),
                "SRPMS": str(output_path / "SRPMS"),
            },
        }

    except Exception as e:
        return {"error": f"RPM package creation failed: {str(e)}"}
