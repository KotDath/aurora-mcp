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

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastmcp import Context

from ..utils import SFDKWrapper

from ..decorators import development_status, DevelopmentStatus

logger = logging.getLogger(__name__)


def truncate_output(output: str, max_lines: int = 50, max_chars: int = 5000) -> str:
    """Truncate command output to avoid token limits while preserving important info.

    Args:
        output: Full command output
        max_lines: Maximum number of lines to keep
        max_chars: Maximum number of characters to keep

    Returns:
        Truncated output with summary
    """
    if not output:
        return output

    lines = output.split("\n")

    # If output is already small, return as-is
    if len(output) <= max_chars and len(lines) <= max_lines:
        return output

    # Take first and last portions
    half_lines = max_lines // 2
    truncated_lines = (
        lines[:half_lines]
        + ["...", f"[Output truncated - {len(lines)} total lines]", "..."]
        + lines[-half_lines:]
    )

    truncated = "\n".join(truncated_lines)

    # If still too long, truncate by characters
    if len(truncated) > max_chars:
        truncated = (
            truncated[: max_chars - 50] + "...\n[Output truncated for response size]"
        )

    return truncated


class QtBuildTool:
    """Qt build tool for Aurora OS projects."""

    def __init__(self, aurora_home: Path):
        self.aurora_home = aurora_home

        # Initialize SFDK wrapper
        self.sfdk = SFDKWrapper(aurora_home)

        # Configure PSDK path from environment or default
        psdk_env = os.getenv("PSDK_AURORA") or os.getenv("PSDK")
        if psdk_env:
            self.psdk_path = Path(psdk_env)
        else:
            self.psdk_path = aurora_home / "psdk"

        # Legacy properties for backward compatibility
        self.sfdk_path = self.sfdk.sfdk_path
        self.build_engine_path = self.sfdk_path

    @development_status(DevelopmentStatus.READY)
    async def build_project(
        self,
        project_path: str,
        build_type: str = "Release",
        target_arch: str = "armv7hl",
        build_tool: Optional[str] = None,
        build_dir_name: str = "build_amogus",
        context: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Build Qt project for Aurora OS using SFDK or PSDK.

        This function compiles Qt applications for Aurora OS. Use it when you need to:
        - Build Qt/QML applications for Aurora OS devices
        - Compile C++/Qt projects with Aurora OS SDK
        - Generate RPM packages for Aurora OS deployment
        - Use SFDK (modern build engine) or PSDK (platform SDK)

        Examples of when to use this tool:
        - "Build my Qt project with SFDK"
        - "Compile the Aurora OS application"
        - "Build project for armv7hl architecture"
        - "Create release build using PSDK"

        Args:
            project_path: **ABSOLUTE** path to Qt project directory (must start with /)
            build_type: Build configuration - "Debug" or "Release" (default: Release)
            target_arch: Target architecture - "armv7hl", "aarch64", or "x86_64" (default: armv7hl)
            build_tool: Build tool preference - "sfdk" (Build Engine), "psdk" (Platform SDK), or None for auto-detect
            build_dir_name: Name of build directory for SFDK builds (default: build_amogus)
            context: FastMCP context for reporting progress (optional)

        Returns:
            Dict containing build result with success status, output logs, and generated artifacts
        """

        async def log_info(message: str):
            """Helper to log info messages"""
            logger.info(message)
            if context:
                await context.info(message)

        async def log_error(message: str):
            """Helper to log error messages"""
            logger.error(message)
            if context:
                await context.error(message)

        await log_info(f"Starting Qt project build...")
        await log_info(f"Project path: {project_path}")
        await log_info(f"Build type: {build_type}, Target arch: {target_arch}")
        await log_info(f"Build tool preference: {build_tool or 'auto-detect'}")

        try:
            project_dir = Path(project_path)

            # Validate that path is absolute
            if not project_dir.is_absolute():
                error_msg = (
                    f"Project path must be absolute (start with /). Got: {project_path}"
                )
                await log_error(error_msg)
                return {"success": False, "error": error_msg}

            # Check if project directory exists
            if not project_dir.exists():
                error_msg = f"Project directory not found: {project_path}"
                await log_error(error_msg)
                return {"success": False, "error": error_msg}

            await log_info("Project directory validated successfully")

            # Detect project type
            await log_info("Detecting project type...")
            project_type = await self._detect_project_type(project_dir)
            await log_info(f"Detected project type: {project_type}")

            # Determine build tool to use
            await log_info("Selecting build tool...")
            selected_tool = await self._select_build_tool(build_tool)
            if not selected_tool["success"]:
                error_msg = f"Build tool selection failed: {selected_tool.get('error')}"
                await log_error(error_msg)
                return selected_tool

            tool_type = selected_tool["tool_type"]
            await log_info(f"Selected build tool: {tool_type}")
            if selected_tool.get("message"):
                await log_info(selected_tool["message"])

            if tool_type == "psdk":
                await log_info("Building with Platform SDK (PSDK)...")
                result = await self._build_with_psdk(
                    project_dir, project_type, build_type, target_arch, context
                )
            elif tool_type == "sfdk":
                await log_info("Building with Sailfish SDK (SFDK)...")
                result = await self._build_with_sfdk(
                    project_dir,
                    project_type,
                    build_type,
                    target_arch,
                    build_dir_name,
                    context,
                )
            else:
                error_msg = f"Unknown build tool: {tool_type}"
                await log_error(error_msg)
                return {"success": False, "error": error_msg}

            # Report final result
            if result.get("success"):
                await log_info(f"Build completed successfully")
            else:
                await log_error(f"Build failed: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            error_msg = f"Error building Qt project: {e}"
            await log_error(error_msg)
            return {"success": False, "error": str(e)}

    async def _detect_project_type(self, project_dir: Path) -> str:
        """Detect Qt project type (CMake or QMake)."""
        if (project_dir / "CMakeLists.txt").exists():
            return "cmake"
        elif list(project_dir.glob("*.pro")):
            return "qmake"
        else:
            return "unknown"

    async def _select_build_tool(
        self, build_tool: Optional[str] = None
    ) -> Dict[str, Any]:
        """Select build tool based on environment variable or auto-detection.

        Args:
            build_tool: Explicit build tool ('sfdk' or 'psdk')

        Returns:
            Selected tool information
        """
        # Get build tool from parameter or environment variable
        selected_tool = build_tool or os.getenv("MCP_BUILD_TOOL", "").lower()

        # Check explicit tool selection
        if selected_tool == "sfdk":
            if await self.sfdk.is_available():
                return {
                    "success": True,
                    "tool_type": "sfdk",
                    "message": "Using SFDK (Build Engine)",
                }
            else:
                return {"success": False, "error": "SFDK requested but not available"}

        elif selected_tool == "psdk":
            if self.psdk_path.exists():
                return {
                    "success": True,
                    "tool_type": "psdk",
                    "message": "Using PSDK (Platform SDK)",
                }
            else:
                return {"success": False, "error": "PSDK requested but not found"}

        # Auto-detection: prefer SFDK (Build Engine), fallback to PSDK
        elif selected_tool == "" or selected_tool is None:
            # Check SFDK first
            if await self.sfdk.is_available():
                return {
                    "success": True,
                    "tool_type": "sfdk",
                    "message": "Auto-detected SFDK (Build Engine)",
                }
            # Fallback to PSDK
            elif self.psdk_path.exists():
                return {
                    "success": True,
                    "tool_type": "psdk",
                    "message": "Auto-detected PSDK (Platform SDK)",
                }
            else:
                return {
                    "success": False,
                    "error": "No build tools available. Please install SFDK (Build Engine) or PSDK (Platform SDK)",
                }

        else:
            return {
                "success": False,
                "error": f"Unknown build tool: {selected_tool}. Use 'sfdk' or 'psdk'",
            }

    async def _build_with_psdk(
        self,
        project_dir: Path,
        project_type: str,
        build_type: str,
        target_arch: str,
        context: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Build project using Platform SDK."""
        logger.info(f"Initializing PSDK build for {project_type} project")
        logger.info(f"Target architecture: {target_arch}")
        logger.info(f"Build type: {build_type}")

        if context:
            await context.info("🏗️ Building with Platform SDK (PSDK)...")
            await context.report_progress(0, 100, "Initializing PSDK build")

        try:
            build_dir = project_dir / f"build-{target_arch}"
            logger.info(f"Creating build directory: {build_dir}")
            build_dir.mkdir(exist_ok=True)

            if context:
                await context.info(f"📂 Created build directory: {build_dir}")
                await context.report_progress(20, 100, "Build directory ready")

            # Prepare PSDK environment
            logger.info("Preparing PSDK environment variables...")
            psdk_env = await self._get_psdk_environment(target_arch)

            if context:
                await context.info("⚙️ Environment configured")
                await context.report_progress(30, 100, "Environment ready")

            if project_type == "cmake":
                logger.info("Building CMake project with PSDK...")
                if context:
                    await context.info("🔨 Running CMake build...")
                result = await self._build_cmake_psdk(
                    project_dir, build_dir, build_type, psdk_env
                )
            elif project_type == "qmake":
                logger.info("Building QMake project with PSDK...")
                if context:
                    await context.info("🔨 Running QMake build...")
                result = await self._build_qmake_psdk(
                    project_dir, build_dir, build_type, psdk_env
                )
            else:
                error_msg = f"Unsupported project type: {project_type}"
                logger.error(error_msg)
                if context:
                    await context.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}

            if result.get("success"):
                logger.info("PSDK build completed successfully")
                if context:
                    await context.info("🎉 PSDK build completed successfully!")
                    await context.report_progress(100, 100, "Build complete")
                result["build_tool"] = "psdk"
            else:
                logger.error(
                    f"PSDK build failed: {result.get('error', 'Unknown error')}"
                )
                if context:
                    await context.error(
                        f"❌ PSDK build failed: {result.get('error', 'Unknown error')}"
                    )

            return result

        except Exception as e:
            logger.error(f"Error building with PSDK: {e}")
            return {"success": False, "error": str(e), "build_tool": "psdk"}

    async def _build_cmake_psdk(
        self, project_dir: Path, build_dir: Path, build_type: str, env: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build CMake project with PSDK."""
        commands = [
            # Configure
            [
                "cmake",
                "-DCMAKE_BUILD_TYPE=" + build_type,
                "-DCMAKE_TOOLCHAIN_FILE=/usr/share/cmake/aurora-platform-toolchain.cmake",
                str(project_dir),
            ],
            # Build
            ["cmake", "--build", ".", "--config", build_type],
        ]

        logger.info(f"Starting CMake build in directory: {build_dir}")

        outputs = []
        commands_executed = []

        for i, cmd in enumerate(commands):
            step_name = "Configuration" if i == 0 else "Build"
            cmd_str = " ".join(cmd)
            logger.info(f"Executing {step_name} step: {cmd_str}")
            commands_executed.append(cmd_str)

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=build_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace")
            outputs.append(output)

            if proc.returncode != 0:
                error_msg = f"{step_name} step failed: {cmd_str}"
                logger.error(error_msg)
                logger.error(f"Command output: {output}")
                return {
                    "success": False,
                    "error": error_msg,
                    "output": truncate_output(output),
                    "commands_executed": commands_executed,
                    "failed_step": step_name.lower(),
                    "output_truncated": len(output) > 5000
                    or len(output.split("\n")) > 50,
                }

            logger.info(f"{step_name} step completed successfully")

        # Find artifacts
        logger.info("Searching for build artifacts...")
        artifacts = await self._find_build_artifacts(build_dir)
        logger.info(f"Found {len(artifacts)} build artifacts")

        # Log full output but truncate for response
        full_output = "\n".join(outputs)
        logger.info(f"Full CMake build output:\n{full_output}")

        return {
            "success": True,
            "build_type": "cmake",
            "output": truncate_output(full_output),
            "artifacts": artifacts,
            "build_dir": str(build_dir),
            "commands_executed": commands_executed,
            "project_dir": str(project_dir),
            "output_truncated": len(full_output) > 5000
            or len(full_output.split("\n")) > 50,
        }

    async def _build_qmake_psdk(
        self, project_dir: Path, build_dir: Path, build_type: str, env: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build QMake project with PSDK."""
        logger.info("Looking for .pro files...")
        pro_files = list(project_dir.glob("*.pro"))
        if not pro_files:
            error_msg = "No .pro file found in project"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        pro_file = pro_files[0]
        logger.info(f"Found .pro file: {pro_file}")

        commands = [
            # Run qmake
            ["qmake", f"CONFIG+={build_type.lower()}", str(pro_file)],
            # Build
            ["make", "-j", str(os.cpu_count() or 4)],
        ]

        logger.info(f"Starting QMake build in directory: {build_dir}")

        outputs = []
        commands_executed = []

        for i, cmd in enumerate(commands):
            step_name = "QMake generation" if i == 0 else "Make build"
            cmd_str = " ".join(cmd)
            logger.info(f"Executing {step_name} step: {cmd_str}")
            commands_executed.append(cmd_str)

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=build_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace")
            outputs.append(output)

            if proc.returncode != 0:
                error_msg = f"{step_name} step failed: {cmd_str}"
                logger.error(error_msg)
                logger.error(f"Command output: {output}")
                return {
                    "success": False,
                    "error": error_msg,
                    "output": truncate_output(output),
                    "commands_executed": commands_executed,
                    "failed_step": step_name.lower().replace(" ", "_"),
                    "pro_file": str(pro_file),
                    "output_truncated": len(output) > 5000
                    or len(output.split("\n")) > 50,
                }

            logger.info(f"{step_name} step completed successfully")

        # Find artifacts
        logger.info("Searching for build artifacts...")
        artifacts = await self._find_build_artifacts(build_dir)
        logger.info(f"Found {len(artifacts)} build artifacts")

        # Log full output but truncate for response
        full_output = "\n".join(outputs)
        logger.info(f"Full QMake build output:\n{full_output}")

        return {
            "success": True,
            "build_type": "qmake",
            "output": truncate_output(full_output),
            "artifacts": artifacts,
            "build_dir": str(build_dir),
            "commands_executed": commands_executed,
            "project_dir": str(project_dir),
            "pro_file": str(pro_file),
            "output_truncated": len(full_output) > 5000
            or len(full_output.split("\n")) > 50,
        }

    async def _build_with_sfdk(
        self,
        project_dir: Path,
        project_type: str,
        build_type: str,
        target_arch: str,
        build_dir_name: str = "build_amogus",
        context: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Build project using SFDK (Build Engine)."""
        logger.info(f"Initializing SFDK build for {project_type} project")
        logger.info(f"Target architecture: {target_arch}")
        logger.info(f"Project directory: {project_dir}")

        try:
            # Use the SFDKWrapper to build the project
            logger.info("Delegating to SFDK wrapper for project build...")
            result = await self.sfdk.build_project(
                project_dir, target_arch, build_dir_name, context
            )

            # Add project type information to the result
            if result["success"]:
                logger.info("SFDK build completed successfully")
                result["build_type"] = f"{project_type}-sfdk"
                result["build_tool"] = "sfdk"
            else:
                logger.error(
                    f"SFDK build failed: {result.get('error', 'Unknown error')}"
                )

            return result

        except Exception as e:
            logger.error(f"Error building with SFDK: {e}")
            return {"success": False, "error": str(e), "build_tool": "sfdk"}

    async def _get_psdk_environment(self, target_arch: str) -> Dict[str, str]:
        """Get PSDK environment variables."""
        env = os.environ.copy()

        # Add PSDK paths
        psdk_target = self.psdk_path / "targets" / f"AuroraOS-{target_arch}"
        if psdk_target.exists():
            env["PSDK_TARGET"] = str(psdk_target)
            env["PKG_CONFIG_PATH"] = str(psdk_target / "usr/lib/pkgconfig")
            env["CMAKE_PREFIX_PATH"] = str(psdk_target / "usr")

        return env

    async def _find_build_artifacts(self, build_dir: Path) -> List[str]:
        """Find build artifacts in build directory."""
        artifacts = []

        # Look for common artifact patterns
        patterns = ["*.rpm", "*.so*", "**/bin/*", "**/lib/*"]

        for pattern in patterns:
            for artifact in build_dir.rglob(pattern):
                if artifact.is_file():
                    artifacts.append(str(artifact))

        return artifacts

    @development_status(DevelopmentStatus.NOT_READY)
    async def configure_environment(
        self, target_arch: str = "armv7hl"
    ) -> Dict[str, Any]:
        """Configure Qt build environment for Aurora OS."""
        try:
            env_info = {
                "target_arch": target_arch,
                "psdk_available": self.psdk_path.exists(),
                "build_engine_available": self.build_engine_path.exists(),
            }

            # Check PSDK targets
            if self.psdk_path.exists():
                targets_dir = self.psdk_path / "targets"
                if targets_dir.exists():
                    env_info["available_targets"] = [
                        t.name for t in targets_dir.iterdir() if t.is_dir()
                    ]

            # Check Qt installation
            qt_info = await self._check_qt_installation(target_arch)
            env_info.update(qt_info)

            return {"success": True, "environment": env_info}

        except Exception as e:
            logger.error(f"Error configuring environment: {e}")
            return {"success": False, "error": str(e)}

    async def _check_qt_installation(self, target_arch: str) -> Dict[str, Any]:
        """Check Qt installation for target architecture."""
        qt_info = {}

        try:
            # Check for qmake
            proc = await asyncio.create_subprocess_exec(
                "qmake",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                qt_info["qmake_available"] = True
                qt_info["qmake_version"] = stdout.decode().strip()
            else:
                qt_info["qmake_available"] = False

        except Exception:
            qt_info["qmake_available"] = False

        return qt_info

    @development_status(DevelopmentStatus.NOT_READY)
    async def list_targets(self) -> Dict[str, Any]:
        """List available Qt build targets."""
        try:
            targets = []

            if self.psdk_path.exists():
                targets_dir = self.psdk_path / "targets"
                if targets_dir.exists():
                    for target in targets_dir.iterdir():
                        if target.is_dir():
                            targets.append(
                                {
                                    "name": target.name,
                                    "path": str(target),
                                    "type": "psdk",
                                }
                            )

            return {"success": True, "targets": targets}

        except Exception as e:
            logger.error(f"Error listing targets: {e}")
            return {"success": False, "error": str(e)}

    @development_status(DevelopmentStatus.NOT_READY)
    async def list_build_tools(self) -> Dict[str, Any]:
        """List available build tools and their status."""
        try:
            tools = []

            # Check SFDK availability using wrapper
            sfdk_available = await self.sfdk.is_available()
            sfdk_info = {
                "name": "SFDK",
                "type": "sfdk",
                "description": "Sailfish SDK Build Engine",
                "available": sfdk_available,
                "priority": 1,
                "path": str(self.sfdk.sfdk_path),
                "command": self.sfdk.get_sfdk_command(),
            }

            if sfdk_available:
                # Get SFDK version using wrapper
                version_result = await self.sfdk.get_version()
                if version_result["success"]:
                    sfdk_info["version"] = version_result["version"]
                else:
                    sfdk_info["version"] = "Unknown"

                # Get SFDK targets using wrapper
                targets_result = await self.sfdk.list_targets()
                if targets_result["success"]:
                    target_names = [t["name"] for t in targets_result["targets"]]
                    sfdk_info["targets"] = target_names
                else:
                    logger.warning(
                        f"Could not get SFDK targets: {targets_result.get('error')}"
                    )
                    sfdk_info["targets"] = []

            tools.append(sfdk_info)

            # Check PSDK availability
            psdk_available = self.psdk_path.exists()
            psdk_info = {
                "name": "PSDK",
                "type": "psdk",
                "description": "Platform SDK",
                "available": psdk_available,
                "priority": 2,
                "path": str(self.psdk_path),
            }

            if psdk_available:
                # Get PSDK targets
                targets_dir = self.psdk_path / "targets"
                if targets_dir.exists():
                    psdk_targets = [
                        t.name
                        for t in targets_dir.iterdir()
                        if t.is_dir() and t.name.startswith("AuroraOS")
                    ]
                    psdk_info["targets"] = psdk_targets
                else:
                    psdk_info["targets"] = []

            tools.append(psdk_info)

            # Determine default tool based on environment variable and availability
            env_tool = os.getenv("MCP_BUILD_TOOL", "").lower()
            if env_tool == "sfdk" and sfdk_available:
                default_tool = "sfdk"
            elif env_tool == "psdk" and psdk_available:
                default_tool = "psdk"
            elif sfdk_available:
                default_tool = "sfdk"
            elif psdk_available:
                default_tool = "psdk"
            else:
                default_tool = None

            # Get environment configuration info
            env_config = {
                "MCP_BUILD_TOOL": env_tool or None,
                "SFDK_AURORA": os.getenv("SFDK_AURORA"),
                "SFDK": os.getenv("SFDK"),
                "PSDK_AURORA": os.getenv("PSDK_AURORA"),
                "PSDK": os.getenv("PSDK"),
                "AURORA_MCP_HOME": os.getenv("AURORA_MCP_HOME"),
            }

            # Remove None values
            env_config = {k: v for k, v in env_config.items() if v is not None}

            return {
                "success": True,
                "tools": tools,
                "default_tool": default_tool,
                "environment_variables": env_config,
                "aurora_home": str(self.aurora_home),
            }

        except Exception as e:
            logger.error(f"Error listing build tools: {e}")
            return {"success": False, "error": str(e)}
