"""
Copyright 2025 Daniil Markevich (KotDath)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# THIS TOOL UNDER DEVELOPMENT

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiofiles
import git

from ..decorators import DevelopmentStatus, development_status

logger = logging.getLogger(__name__)


class TemplateTool:
    """Template management tool for Aurora OS project creation."""

    def __init__(self, aurora_home: Path):
        self.aurora_home = aurora_home
        self.templates_cache = aurora_home / "templates"
        self.templates_cache.mkdir(exist_ok=True)

        # Default Aurora OS templates
        self.default_templates = {
            "application": "https://gitlab.com/omprussia/demos/ApplicationTemplate",
            "qt-quick": "https://gitlab.com/omprussia/demos/QtQuickTemplate",
            "qml-app": "https://gitlab.com/omprussia/demos/QMLAppTemplate",
        }

    @development_status(DevelopmentStatus.NOT_READY)
    async def create_project(
        self,
        template_name: str,
        project_name: str,
        output_dir: str = ".",
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a new project from template.

        Args:
            template_name: Template identifier
            project_name: Name for the new project
            output_dir: Directory to create project in
            variables: Template variables to substitute

        Returns:
            Creation result with status and project information
        """
        try:
            output_path = Path(output_dir)
            project_path = output_path / project_name

            if project_path.exists():
                return {
                    "success": False,
                    "error": f"Project directory already exists: {project_path}",
                }

            # Download or find template
            template_result = await self._download_template(template_name)
            if not template_result["success"]:
                return template_result

            template_dir = Path(template_result["template_path"])

            # Create project directory
            project_path.mkdir(parents=True)

            # Copy and customize template
            customize_result = await self._customize_template(
                template_dir, project_path, project_name, variables or {}
            )

            if not customize_result["success"]:
                return customize_result

            # Initialize git repository if requested
            git_result = await self._init_git_repo(project_path)

            return {
                "success": True,
                "project_path": str(project_path),
                "template_used": template_name,
                "files_created": customize_result["files_processed"],
                "git_initialized": git_result["success"],
            }

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return {"success": False, "error": str(e)}

    async def _download_template(self, template_url: str) -> dict[str, Any]:
        """Download template from GitLab repository."""
        try:
            # Parse URL to get repo name
            parsed = urlparse(template_url)
            repo_name = Path(parsed.path).name
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

            template_path = self.templates_cache / repo_name

            # Check if template is already cached
            if template_path.exists():
                # Update existing template
                try:
                    repo = git.Repo(template_path)
                    repo.remotes.origin.pull()
                    logger.info(f"Updated cached template: {repo_name}")
                except Exception as e:
                    logger.warning(f"Could not update template {repo_name}: {e}")
            else:
                # Clone new template
                repo = git.Repo.clone_from(template_url, template_path)
                logger.info(f"Downloaded template: {repo_name}")

            return {
                "success": True,
                "template_path": template_path,
                "template_name": repo_name,
            }

        except Exception as e:
            logger.error(f"Error downloading template: {e}")
            return {"success": False, "error": f"Failed to download template: {e}"}

    async def _customize_template(
        self,
        template_path: Path,
        output_path: Path,
        project_name: str,
        template_vars: dict[str, str],
    ) -> dict[str, Any]:
        """Customize template with project-specific values."""
        try:
            # Copy template files
            import shutil

            shutil.copytree(
                template_path,
                output_path,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )

            # Default template variables
            vars_dict = {
                "PROJECT_NAME": project_name,
                "PROJECT_NAME_UPPER": project_name.upper(),
                "PROJECT_NAME_LOWER": project_name.lower(),
                **template_vars,
            }

            # Process template files
            await self._process_template_files(output_path, vars_dict)

            # Rename files if needed
            await self._rename_template_files(output_path, project_name)

            return {
                "success": True,
                "customized_files": await self._count_processed_files(output_path),
            }

        except Exception as e:
            logger.error(f"Error customizing template: {e}")
            return {"success": False, "error": f"Failed to customize template: {e}"}

    async def _process_template_files(
        self, project_path: Path, vars_dict: dict[str, str]
    ):
        """Process template files and replace variables."""
        # File extensions to process
        text_extensions = {
            ".cpp",
            ".h",
            ".hpp",
            ".c",
            ".cc",
            ".cxx",
            ".py",
            ".js",
            ".ts",
            ".qml",
            ".pro",
            ".pri",
            ".cmake",
            ".txt",
            ".md",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".conf",
            ".spec",
        }

        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in text_extensions:
                try:
                    async with aiofiles.open(file_path, encoding="utf-8") as f:
                        content = await f.read()

                    # Replace template variables
                    modified = False
                    for var_name, var_value in vars_dict.items():
                        placeholder = f"{{{{ {var_name} }}}}"
                        if placeholder in content:
                            content = content.replace(placeholder, var_value)
                            modified = True

                        # Also try without spaces
                        placeholder = f"{{{{{var_name}}}}}"
                        if placeholder in content:
                            content = content.replace(placeholder, var_value)
                            modified = True

                    if modified:
                        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                            await f.write(content)

                except Exception as e:
                    logger.warning(f"Could not process file {file_path}: {e}")

    async def _rename_template_files(self, project_path: Path, project_name: str):
        """Rename files that contain template placeholders."""
        # Find files with template names
        template_patterns = ["template", "Template", "TEMPLATE"]

        for pattern in template_patterns:
            for file_path in project_path.rglob(f"*{pattern}*"):
                if file_path.is_file():
                    new_name = file_path.name.replace(pattern, project_name)
                    new_path = file_path.parent / new_name

                    if new_path != file_path:
                        try:
                            file_path.rename(new_path)
                            logger.info(f"Renamed {file_path.name} to {new_name}")
                        except Exception as e:
                            logger.warning(f"Could not rename {file_path}: {e}")

    async def _count_processed_files(self, project_path: Path) -> int:
        """Count processed files in project."""
        count = 0
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                count += 1
        return count

    async def _init_git_repo(self, project_path: Path) -> dict[str, Any]:
        """Initialize git repository in project."""
        try:
            # Initialize git repo
            repo = git.Repo.init(project_path)

            # Create initial commit
            repo.index.add_to_index(["*"])
            repo.index.commit("Initial commit from Aurora OS template")

            return {"success": True, "message": "Git repository initialized"}

        except Exception as e:
            logger.warning(f"Could not initialize git repository: {e}")
            return {"success": False, "error": str(e)}

    @development_status(DevelopmentStatus.NOT_READY)
    async def list_templates(self) -> dict[str, Any]:
        """List available project templates.

        Returns:
            Available templates with their descriptions
        """
        try:
            templates = []

            # Add default templates
            for template_id, info in self.default_templates.items():
                templates.append(
                    {
                        "id": template_id,
                        "name": info["name"],
                        "description": info["description"],
                        "type": "default",
                        "url": info["url"],
                    }
                )

            # Check for cached templates
            if self.templates_cache.exists():
                cache_templates = list(self.templates_cache.iterdir())
                for template_dir in cache_templates:
                    if template_dir.is_dir():
                        meta_file = template_dir / "template.json"
                        if meta_file.exists():
                            try:
                                import json

                                with open(meta_file) as f:
                                    meta = json.load(f)
                                templates.append(
                                    {
                                        "id": template_dir.name,
                                        "name": meta.get("name", template_dir.name),
                                        "description": meta.get(
                                            "description", "Custom template"
                                        ),
                                        "type": "cached",
                                        "path": str(template_dir),
                                    }
                                )
                            except Exception:
                                # Skip invalid template metadata
                                continue

            return {"success": True, "templates": templates}

        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return {"success": False, "error": str(e)}

    @development_status(DevelopmentStatus.NOT_READY)
    async def update_template_cache(self) -> dict[str, Any]:
        """Update template cache from remote sources.

        Returns:
            Update result with status and statistics
        """
        try:
            updated_templates = []
            errors = []

            for template_id, info in self.default_templates.items():
                try:
                    result = await self._download_template(template_id)
                    if result["success"]:
                        updated_templates.append(template_id)
                    else:
                        errors.append(f"{template_id}: {result['error']}")
                except Exception as e:
                    errors.append(f"{template_id}: {str(e)}")

            return {
                "success": len(errors) == 0,
                "updated_templates": updated_templates,
                "errors": errors,
                "cache_path": str(self.templates_cache),
            }

        except Exception as e:
            logger.error(f"Error updating template cache: {e}")
            return {"success": False, "error": str(e)}
