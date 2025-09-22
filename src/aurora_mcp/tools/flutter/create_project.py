import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

from fastmcp import Context

# Flutter template URL mapping
FLUTTER_TEMPLATES = {
    "app": "https://gitlab.com/omprussia/flutter/templates/app_template",
    "dbus_plugin": "https://gitlab.com/omprussia/flutter/templates/dbus_template",
    "ffi_plugin": "https://gitlab.com/omprussia/flutter/templates/ffi_template",
    "platform_plugin": "https://gitlab.com/omprussia/flutter/templates/platform_channel_template",
    "interface_plugin": "https://gitlab.com/omprussia/flutter/templates/platform_interface_template",
}

# Local template directory mapping
LOCAL_FLUTTER_TEMPLATES = {
    "app": "app_template",
    "dbus_plugin": "dbus_template",
    "ffi_plugin": "ffi_template",
    "platform_plugin": "platform_channel_template",
    "interface_plugin": "platform_interface_template",
}


def _validate_organization_name(org_name: str) -> bool:
    """Validate organization name format: <domain>.<organization>"""
    pattern = r"^[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+$"
    return bool(re.match(pattern, org_name))


async def _replace_in_files(project_dir: Path, old_text: str, new_text: str) -> None:
    """Replace text in all files recursively"""
    if old_text == new_text:
        return

    for file_path in project_dir.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith(".git"):
            try:
                content = file_path.read_text(encoding="utf-8")
                if old_text in content:
                    new_content = content.replace(old_text, new_text)
                    file_path.write_text(new_content, encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files without read permissions
                continue


async def _rename_files(project_dir: Path, old_name: str, new_name: str) -> None:
    """Rename files containing old_name to new_name"""
    if old_name == new_name:
        return

    files_to_rename = []
    for file_path in project_dir.rglob("*"):
        if file_path.is_file() and old_name in file_path.name:
            files_to_rename.append(file_path)

    for file_path in files_to_rename:
        new_file_name = file_path.name.replace(old_name, new_name)
        new_file_path = file_path.parent / new_file_name
        file_path.rename(new_file_path)


async def create_flutter_project(
    ctx: Context,
    workspace_dir: str,
    type: Literal[
        "app", "dbus_plugin", "ffi_plugin", "platform_plugin", "interface_plugin"
    ],
    organization_name: str = "ru.auroraos",
    application_name: str = "ApplicationTemplate",
) -> dict[str, Any]:
    """Create Flutter project for Aurora OS from GitLab template.

    This tool clones the appropriate Flutter template repository from omprussia GitLab
    and customizes it with your organization name and application name.
    The project contents will be placed directly in the specified workspace directory.

    Args:
        ctx: FastMCP context
        type: Project type - app, dbus_plugin, ffi_plugin, platform_plugin, or interface_plugin
        organization_name: Organization identifier in format <domain>.<organization> (default: ru.auroraos)
        application_name: Application name (default: ApplicationTemplate)
        workspace_dir: Absolute path to directory where to place the project contents

    Returns:
        Dict with status, project details, and next steps
    """
    try:
        # Validate type
        valid_types = [
            "app",
            "dbus_plugin",
            "ffi_plugin",
            "platform_plugin",
            "interface_plugin",
        ]
        if type not in valid_types:
            return {
                "error": f"Invalid project type. Must be one of: {', '.join(valid_types)}",
                "valid_types": valid_types,
            }

        # Validate organization name format
        if not _validate_organization_name(organization_name):
            return {
                "error": "Invalid organization name format. Must be <domain>.<organization> (e.g., 'ru.auroraos', 'com.mycompany')",
                "organization_name": organization_name,
                "expected_format": "<domain>.<organization>",
            }

        # Validate workspace_dir is absolute path
        if not Path(workspace_dir).is_absolute():
            return {
                "error": "Workspace directory must be an absolute path",
                "workspace_dir": workspace_dir,
                "note": "Please provide an absolute path like '/home/user/projects' instead of relative path",
            }

        # Prepare repository details
        repo_url = FLUTTER_TEMPLATES[type]
        branch = "example"

        # Convert workspace_dir to Path and resolve
        target_dir = Path(workspace_dir).resolve()

        # Check if target directory exists
        if not target_dir.exists():
            return {
                "error": f"Workspace directory '{workspace_dir}' does not exist",
                "workspace_dir": workspace_dir,
                "resolved_path": str(target_dir),
            }

        # Create temporary directory for cloning
        clone_successful = False
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            clone_target = temp_path / "repo"

            # Clone repository to temporary directory
            clone_command = ["git", "clone", "-b", branch, repo_url, str(clone_target)]
            try:
                subprocess.run(
                    clone_command, capture_output=True, text=True, check=True
                )
                clone_successful = True
            except subprocess.CalledProcessError as e:
                # Try to use local templates as fallback
                template_dir = (
                    Path(__file__).parent.parent.parent.parent.parent
                    / "local_templates"
                    / "flutter"
                )
                local_template_path = template_dir / LOCAL_FLUTTER_TEMPLATES[type]

                if local_template_path.exists():
                    # Copy from local templates instead
                    shutil.copytree(local_template_path, clone_target)
                    clone_successful = True
                else:
                    return {
                        "error": f"Failed to clone repository and no local templates found: {e.stderr}",
                        "repo_url": repo_url,
                        "branch": branch,
                        "clone_command": " ".join(clone_command),
                        "workspace_dir": workspace_dir,
                        "local_template_path": str(local_template_path),
                        "note": "Please check network connection, repository access, or ensure local templates exist",
                    }
            except FileNotFoundError:
                return {
                    "error": "Git command not found. Please install Git.",
                    "required_command": "git",
                }

            # Check for conflicts before copying
            conflicts = []
            for item in clone_target.iterdir():
                if item.name == ".git":
                    # Skip .git directory
                    continue
                dest = target_dir / item.name
                if dest.exists():
                    conflicts.append(item.name)

            if conflicts:
                return {
                    "error": "Cannot create project: conflicting files/directories already exist",
                    "conflicts": conflicts,
                    "workspace_dir": workspace_dir,
                    "note": "Please remove or rename the conflicting items and try again",
                }

            # Move contents from cloned repo to target directory
            for item in clone_target.iterdir():
                if item.name == ".git":
                    # Skip .git directory
                    continue
                dest = target_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

        # Perform replacements if values are not default
        await _replace_in_files(target_dir, "ApplicationTemplate", application_name)
        await _replace_in_files(target_dir, "ru.auroraos", organization_name)

        # Rename files if application name is not default
        await _rename_files(target_dir, "ApplicationTemplate", application_name)

        # Rename files if organization name is not default (for files containing organization name)
        await _rename_files(target_dir, "ru.auroraos", organization_name)

        # Determine the source used for the project
        source_info = {"url": repo_url, "branch": branch}
        if not clone_successful:
            template_dir = (
                Path(__file__).parent.parent.parent.parent.parent
                / "local_templates"
                / "flutter"
            )
            local_template_path = template_dir / LOCAL_FLUTTER_TEMPLATES[type]
            source_info = {
                "source": "local_template",
                "path": str(local_template_path),
                "note": "Used local template due to network/repository issues",
            }

        return {
            "status": "success",
            "message": f"Successfully created Flutter {type} project '{application_name}' in workspace directory",
            "project_type": type,
            "organization_name": organization_name,
            "application_name": application_name,
            "project_path": str(target_dir),
            "workspace_dir": workspace_dir,
            "repository": source_info,
            "customizations": {
                "replaced_app_name": application_name != "ApplicationTemplate",
                "replaced_org_name": organization_name != "ru.auroraos",
                "renamed_files": application_name != "ApplicationTemplate"
                or organization_name != "ru.auroraos",
            },
            "next_steps": [
                "Review and modify the project as needed",
                "Run 'flutter pub get' to install dependencies",
                "Build the project using Aurora MCP Flutter build tools",
            ],
        }

    except Exception as e:
        return {
            "error": f"Unexpected error creating Flutter project: {str(e)}",
            "project_type": type,
            "organization_name": organization_name,
            "application_name": application_name,
        }
