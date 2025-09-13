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

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastmcp import FastMCP, Context
from fastmcp.utilities.logging import configure_logging

from aurora_mcp.tools.qt_build_tool import QtBuildTool
from aurora_mcp.tools.flutter_build_tool import FlutterBuildTool
from aurora_mcp.tools.rpm_packaging_tool import RPMPackagingTool
from aurora_mcp.tools.template_tool import TemplateTool
from aurora_mcp.tools.conan_tool import ConanTool

# Configure logging
configure_logging(
    level=logging.INFO,
    enable_rich_tracebacks=True,
)

logger = logging.getLogger(__name__)


class AuroraMCP:
    """Aurora OS MCP Server for development tools."""

    def __init__(self, aurora_home: Optional[str] = None):
        self.aurora_home = Path(aurora_home or "/opt/aurora-os")
        self.mcp = FastMCP("AuroraMCP")
        self._setup_server()

    def _setup_server(self):
        """Setup FastMCP server with Aurora OS development tools."""

        # Initialize tools
        self.qt_tool = QtBuildTool(self.aurora_home)
        self.flutter_tool = FlutterBuildTool(self.aurora_home)
        self.rpm_tool = RPMPackagingTool(self.aurora_home)
        self.template_tool = TemplateTool(self.aurora_home)
        self.conan_tool = ConanTool(self.aurora_home)

        # Register Qt Build Tools
        self._register_qt_tools()

        # Register Flutter Build Tools
        self._register_flutter_tools()

        # Register RPM Packaging Tools
        self._register_rpm_tools()

        # Register Template Tools
        self._register_template_tools()

        # Register Conan Tools
        self._register_conan_tools()

        # Add server info
        self._add_server_info()

    def _register_qt_tools(self):
        """Register Qt development tools."""

        @self.mcp.tool
        async def build_qt_project(
            ctx: Context,
            project_path: str,
            build_type: str = "Release",
            target_arch: str = "armv7hl",
            build_tool: Optional[str] = None,
            build_dir_name: str = "build_amogus",
        ) -> Dict[str, Any]:
            """Build Qt project for Aurora OS.

            Args:
                project_path: Path to Qt project directory
                build_type: Build type (Debug/Release)
                target_arch: Target architecture (armv7hl, aarch64, x86_64)
                build_tool: Build tool to use ('sfdk' for Build Engine, 'psdk' for Platform SDK, or None for auto-detect)
                build_dir_name: Name of build directory for SFDK builds (default: build_amogus)
            """
            return await self.qt_tool.build_project(
                project_path, build_type, target_arch, build_tool, build_dir_name, ctx
            )

        @self.mcp.tool
        async def configure_qt_environment(
            ctx: Context, target_arch: str = "armv7hl"
        ) -> Dict[str, Any]:
            """Configure Qt build environment for Aurora OS.

            Args:
                target_arch: Target architecture
            """
            return await self.qt_tool.configure_environment(target_arch)

        @self.mcp.tool
        async def list_qt_targets(ctx: Context) -> Dict[str, Any]:
            """List available Qt build targets."""
            return await self.qt_tool.list_targets()

        @self.mcp.tool
        async def list_build_tools(ctx: Context) -> Dict[str, Any]:
            """List available build tools and their status."""
            return await self.qt_tool.list_build_tools()

    def _register_flutter_tools(self):
        """Register Flutter development tools."""

        @self.mcp.tool
        async def build_flutter_project(
            ctx: Context, project_path: str, target_arch: str = "armv7hl"
        ) -> Dict[str, Any]:
            """Build Flutter project for Aurora OS.

            Args:
                project_path: Path to Flutter project
                target_arch: Target architecture
            """
            return await self.flutter_tool.build_project(project_path, target_arch)

        @self.mcp.tool
        async def setup_flutter_embedder(
            ctx: Context, target_arch: str = "armv7hl"
        ) -> Dict[str, Any]:
            """Setup Flutter embedder for Aurora OS.

            Args:
                target_arch: Target architecture
            """
            return await self.flutter_tool.setup_embedder(target_arch)

    def _register_rpm_tools(self):
        """Register RPM packaging tools."""

        @self.mcp.tool
        async def create_rpm_package(
            ctx: Context,
            spec_file: str,
            source_dir: str,
            output_dir: str = "/tmp/rpmbuild",
        ) -> Dict[str, Any]:
            """Create RPM package from spec file.

            Args:
                spec_file: Path to RPM spec file
                source_dir: Source directory
                output_dir: Output directory for RPM
            """
            return await self.rpm_tool.create_package(spec_file, source_dir, output_dir)

        @self.mcp.tool
        async def sign_rpm_package(
            ctx: Context, rpm_file: str, key_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """Sign RPM package.

            Args:
                rpm_file: Path to RPM file
                key_id: GPG key ID for signing
            """
            return await self.rpm_tool.sign_package(rpm_file, key_id)

        @self.mcp.tool
        async def validate_rpm_package(ctx: Context, rpm_file: str) -> Dict[str, Any]:
            """Validate RPM package.

            Args:
                rpm_file: Path to RPM file
            """
            return await self.rpm_tool.validate_package(rpm_file)

    def _register_template_tools(self):
        """Register template management tools."""

        @self.mcp.tool
        async def create_project_from_template(
            ctx: Context,
            template_url: str,
            project_name: str,
            output_dir: str,
            template_vars: Optional[Dict[str, str]] = None,
        ) -> Dict[str, Any]:
            """Create new project from GitLab template.

            Args:
                template_url: GitLab template URL
                project_name: New project name
                output_dir: Output directory
                template_vars: Template variables for customization
            """
            return await self.template_tool.create_project(
                template_url, project_name, output_dir, template_vars or {}
            )

        @self.mcp.tool
        async def list_available_templates(ctx: Context) -> Dict[str, Any]:
            """List available Aurora OS templates."""
            return await self.template_tool.list_templates()

    def _register_conan_tools(self):
        """Register Conan package management tools."""

        @self.mcp.tool
        async def install_conan_dependencies(
            ctx: Context, conanfile_path: str, profile: Optional[str] = None
        ) -> Dict[str, Any]:
            """Install Conan dependencies.

            Args:
                conanfile_path: Path to conanfile.txt or conanfile.py
                profile: Conan profile to use
            """
            return await self.conan_tool.install_dependencies(conanfile_path, profile)

        @self.mcp.tool
        async def create_conan_package(
            ctx: Context, recipe_path: str, package_reference: str
        ) -> Dict[str, Any]:
            """Create Conan package.

            Args:
                recipe_path: Path to conanfile.py
                package_reference: Package reference
            """
            return await self.conan_tool.create_package(recipe_path, package_reference)

    def _add_server_info(self):
        """Add server information and health check."""

        @self.mcp.tool
        async def aurora_mcp_info(ctx: Context) -> Dict[str, Any]:
            """Get Aurora MCP server information."""
            return {
                "server": "Aurora MCP",
                "version": "0.1.0",
                "aurora_home": str(self.aurora_home),
                "available_tools": [
                    "Qt Build Tools",
                    "Flutter Build Tools",
                    "RPM Packaging Tools",
                    "Template Management Tools",
                    "Conan Integration Tools",
                ],
                "supported_architectures": ["armv7hl", "aarch64", "x86_64"],
            }

        @self.mcp.tool
        async def check_aurora_environment(ctx: Context) -> Dict[str, Any]:
            """Check Aurora OS development environment status."""
            status = {
                "psdk_available": (self.aurora_home / "psdk").exists(),
                "build_engine_available": (self.aurora_home / "build-engine").exists(),
                "projects_dir": (self.aurora_home / "projects").exists(),
            }

            # Check for Aurora CLI
            try:
                import shutil

                status["aurora_cli"] = shutil.which("aurora-cli") is not None
            except Exception:
                status["aurora_cli"] = False

            return status

    def get_server(self) -> FastMCP:
        """Get the FastMCP server instance."""
        return self.mcp


# Create server instance
def create_server(aurora_home: Optional[str] = None) -> FastMCP:
    """Create and return Aurora MCP server instance."""
    aurora_mcp = AuroraMCP(aurora_home)
    return aurora_mcp.get_server()


# For direct execution
if __name__ == "__main__":
    import os

    aurora_home = os.getenv("AURORA_MCP_HOME", "/opt/aurora-os")
    server = create_server(aurora_home)

    logger.info(f"Starting Aurora MCP server with Aurora home: {aurora_home}")

    # Run server
    asyncio.run(server.run())
