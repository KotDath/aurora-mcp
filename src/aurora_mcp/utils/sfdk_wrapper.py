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
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SFDKOutputFilter:
    """Filter SFDK output to show only important messages."""

    def __init__(self):
        # Patterns for important messages to show
        self.show_patterns = [
            r"NOTICE:",
            r"WARNING:",
            r"ERROR:",
            r"Loading repository data\.\.\.",
            r"Building target platforms:",
            r"Building for target",
            r"Executing\(%build\):",
            r"Executing\(%install\):",
            r"Wrote:\s+.*\.rpm",
            r"Processing files:",
            r"RPM_EC=",
            # Compilation progress indicators
            r"\[\s*\d+%\]",
            r"-- \w+:",
            r"CMake",
        ]

        # Patterns for messages to hide (spam)
        self.hide_patterns = [
            r"'[^']+' not found in package names\. Trying capabilities\.",
            r"'[^']+' providing '[^']+' is already installed\.",
            r"'[^']+' is already installed\.",
            r"No update candidate for",
            r"The highest available version is already installed\.",
            r"Resolving package dependencies\.\.\.",
            r"Nothing to do\.",
            r"Requires\(rpmlib\):",
            r"Requires:",
            r"Provides:",
            r"^\+\s+/.*",  # RPM build script lines starting with +
            r"^\s*$",  # Empty lines
        ]

        self.show_compiled = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.show_patterns
        ]
        self.hide_compiled = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.hide_patterns
        ]

    def should_show_line(self, line: str) -> bool:
        """Determine if a line should be shown to the user."""
        line = line.strip()

        if not line:
            return False

        # Check if line should be hidden first
        for pattern in self.hide_compiled:
            if pattern.search(line):
                return False

        # Check if line should be shown
        for pattern in self.show_compiled:
            if pattern.search(line):
                return True

        # Default: show if it looks like an error or important message
        if any(
            keyword in line.upper()
            for keyword in ["ERROR", "FAILED", "FATAL", "CRITICAL"]
        ):
            return True

        return False

    def get_progress_from_line(self, line: str) -> tuple[float, str] | None:
        """Extract progress percentage and description from build output if available.

        Returns:
            Tuple of (progress_percentage, description) or None
        """
        # Look for percentage indicators like [25%]
        percentage_match = re.search(r"\[\s*(\d+)%\]", line)
        if percentage_match:
            percent = float(percentage_match.group(1))
            # Map cmake percentage to our range (30-80%)
            mapped_percent = 30 + (
                percent * 0.5
            )  # Scale cmake 0-100% to our 30-80% range
            return (mapped_percent, f"Building ({percent}%)")

        # Look for specific build phases and estimate progress
        if "Loading repository data" in line:
            return (22.0, "Loading package repository")
        elif "Reading installed packages" in line:
            return (24.0, "Checking installed packages")
        elif "Resolving package dependencies" in line:
            return (26.0, "Resolving dependencies")
        elif "Building target platforms" in line:
            return (30.0, "Preparing build environment")
        elif "Building for target" in line:
            return (32.0, "Starting compilation")
        elif "Executing(%build)" in line:
            return (35.0, "Running build script")
        elif "CMake" in line and "configuration" in line.lower():
            return (37.0, "Configuring CMake")
        elif "CMake" in line and (
            "build" in line.lower() or "compiling" in line.lower()
        ):
            return (40.0, "CMake compilation")
        elif "Executing(%install)" in line:
            return (75.0, "Installing files")
        elif "Processing files:" in line:
            return (85.0, "Processing package files")
        elif "Provides:" in line:
            return (88.0, "Generating package metadata")
        elif "Requires:" in line:
            return (90.0, "Calculating dependencies")
        elif "Checking for unpackaged file" in line:
            return (92.0, "Validating package")
        elif "Wrote:" in line and ".rpm" in line:
            return (95.0, "RPM package created")
        elif "RPM_EC=0" in line:
            return (98.0, "Build completed successfully")

        return None


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


class SFDKWrapper:
    """Wrapper class for SFDK (Sailfish SDK) operations."""

    def __init__(self, aurora_home: Path | None = None):
        """Initialize SFDK wrapper.

        Args:
            aurora_home: Path to Aurora OS installation directory
        """
        self.aurora_home = aurora_home or Path("/opt/aurora-os")

        # Configure SFDK path from environment or default
        sfdk_env = os.getenv("SFDK_AURORA") or os.getenv("SFDK")
        if sfdk_env:
            self.sfdk_path = Path(sfdk_env)
        else:
            self.sfdk_path = self.aurora_home / "build-engine"

    def get_sfdk_command(self) -> str:
        """Get SFDK command path.

        Returns:
            Path to SFDK executable
        """
        # Check for ~/AuroraOS/bin/sfdk (standard installation path)
        aurora_sfdk = Path.home() / "AuroraOS" / "bin" / "sfdk"
        if aurora_sfdk.exists():
            return str(aurora_sfdk)

        # If SFDK path is configured and contains sfdk binary, use it
        if self.sfdk_path.exists() and (self.sfdk_path / "bin" / "sfdk").exists():
            return str(self.sfdk_path / "bin" / "sfdk")
        elif self.sfdk_path.exists() and (self.sfdk_path / "sfdk").exists():
            return str(self.sfdk_path / "sfdk")
        else:
            # Use system sfdk command
            return "sfdk"

    async def is_available(self) -> bool:
        """Check if SFDK is available.

        Returns:
            True if SFDK is available, False otherwise
        """
        try:
            sfdk_command = self.get_sfdk_command()

            # Check if sfdk command is available
            proc = await asyncio.create_subprocess_exec(
                sfdk_command,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, _ = await proc.communicate()

            # Also check if SFDK directory exists
            return proc.returncode == 0 or self.sfdk_path.exists()

        except (FileNotFoundError, PermissionError):
            # Check SFDK directory as fallback
            return self.sfdk_path.exists()

    async def get_version(self) -> dict[str, Any]:
        """Get SFDK version information.

        Returns:
            Dictionary with version information or error
        """
        try:
            sfdk_command = self.get_sfdk_command()

            proc = await asyncio.create_subprocess_exec(
                sfdk_command,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return {
                    "success": True,
                    "version": stdout.decode().strip(),
                    "command": sfdk_command,
                }
            else:
                return {"success": False, "error": stderr.decode().strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_targets(self) -> dict[str, Any]:
        """List available SFDK build targets.

        Returns:
            Dictionary with targets list or error
        """
        try:
            sfdk_command = self.get_sfdk_command()

            proc = await asyncio.create_subprocess_exec(
                sfdk_command,
                "tools",
                "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": f"Could not list SFDK targets: {stderr.decode()}",
                }

            output = stdout.decode()
            targets = self._parse_targets_output(output)

            return {"success": True, "targets": targets, "raw_output": output}

        except Exception as e:
            logger.error(f"Error listing SFDK targets: {e}")
            return {"success": False, "error": str(e)}

    def _parse_targets_output(self, output: str) -> list[dict[str, Any]]:
        """Parse SFDK tools list output to extract targets.

        Args:
            output: Raw output from 'sfdk tools list'

        Returns:
            List of target dictionaries
        """
        targets = []
        lines = output.split("\n")

        for line in lines:
            original_line = line
            # Clean tree symbols for parsing
            line_clean = (
                line.replace("├── ", "").replace("└── ", "").replace("│   ", "").strip()
            )

            if not line_clean or line_clean.startswith("#"):
                continue

            # Look for Aurora OS targets with architecture
            if "AuroraOS" in line_clean:
                parts = line_clean.split()
                if parts:
                    target_name = parts[0]

                    # Skip snapshots (they have .default suffix)
                    if ".default" in target_name or "snapshot" in original_line:
                        continue

                    # Extract architecture - be more specific with matching
                    arch = None
                    if "-armv7hl" in target_name:
                        arch = "armv7hl"
                    elif "-aarch64" in target_name:
                        arch = "aarch64"
                    elif "-x86_64" in target_name:
                        arch = "x86_64"
                    elif "-i486" in target_name:
                        arch = "x86_64"

                    if arch:
                        target_info = {
                            "name": target_name,
                            "architecture": arch,
                            "installed": "installed" in original_line,
                            "latest": "latest" in original_line,
                        }
                        targets.append(target_info)

        return targets

    async def get_target_for_arch(self, target_arch: str) -> str | None:
        """Get SFDK target name for architecture.

        Maps user-provided architecture to actual SFDK target names:
        - armv7hl -> AuroraOS-X.X.X.X-MB2-armv7hl (or base variant)
        - aarch64 -> AuroraOS-X.X.X.X-MB2-aarch64 (or base variant)
        - x86_64 -> AuroraOS-X.X.X.X-MB2-x86_64 (or base variant)

        Args:
            target_arch: Target architecture (armv7hl, aarch64, x86_64)

        Returns:
            SFDK target name or None if not found
        """
        targets_result = await self.list_targets()

        if not targets_result["success"]:
            logger.warning(
                f"Could not list SFDK targets: {targets_result.get('error')}"
            )
            return None

        targets = targets_result["targets"]

        matching_targets = [t for t in targets if t["architecture"] == target_arch]

        if not matching_targets:
            logger.warning(f"No targets found for architecture: {target_arch}")
            return None

        # Prefer latest installed targets, then any latest, then any installed
        for target in matching_targets:
            if target.get("installed") and target.get("latest"):
                return target["name"]

        for target in matching_targets:
            if target.get("latest"):
                return target["name"]

        for target in matching_targets:
            if target.get("installed"):
                return target["name"]

        # Return first available target
        return matching_targets[0]["name"]

    async def configure_target(self, target_name: str) -> dict[str, Any]:
        """Configure SFDK target for building.

        Args:
            target_name: Name of the SFDK target to configure

        Returns:
            Dictionary with configuration result
        """
        try:
            sfdk_command = self.get_sfdk_command()

            # Set the target using sfdk config
            cmd = [sfdk_command, "config", f"target={target_name}"]

            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return {
                    "success": True,
                    "message": f"Target {target_name} configured successfully",
                    "output": stdout.decode().strip(),
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode().strip(),
                    "command": " ".join(cmd),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_command_streaming(
        self,
        args: list[str],
        cwd: Path | None = None,
        context: Any | None = None,  # FastMCP Context
        show_output: bool = True,
    ) -> dict[str, Any]:
        """Execute SFDK command with streaming output and real-time context updates.

        Args:
            args: Command arguments (without 'sfdk' prefix)
            cwd: Working directory for command execution
            context: FastMCP context for real-time updates
            show_output: Whether to show filtered output via context

        Returns:
            Dictionary with command result
        """
        try:
            sfdk_command = self.get_sfdk_command()
            cmd = [sfdk_command] + args

            output_filter = SFDKOutputFilter()
            output_lines = []

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            )

            # Stream output line by line
            while True:
                try:
                    line_bytes = await proc.stdout.readline()
                    if not line_bytes:
                        break

                    line = line_bytes.decode("utf-8", errors="replace").rstrip()
                    output_lines.append(line)

                    if show_output and context and output_filter.should_show_line(line):
                        # Send important messages to context
                        await context.info(line)

                    # Check for progress updates (even for lines we don't show)
                    if context:
                        progress_info = output_filter.get_progress_from_line(line)
                        if progress_info is not None:
                            progress, description = progress_info
                            await context.report_progress(progress, 100, description)

                except Exception as e:
                    logger.error(f"Error reading line: {e}")
                    break

            # Wait for process to finish
            returncode = await proc.wait()

            full_output = "\n".join(output_lines)

            return {
                "success": returncode == 0,
                "returncode": returncode,
                "output": full_output,
                "command": " ".join(cmd),
                "cwd": str(cwd) if cwd else None,
            }

        except Exception as e:
            logger.error(f"Error executing SFDK command with streaming: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": " ".join([self.get_sfdk_command()] + args),
            }

    async def execute_command(
        self, args: list[str], cwd: Path | None = None
    ) -> dict[str, Any]:
        """Execute SFDK command with error handling.

        Args:
            args: Command arguments (without 'sfdk' prefix)
            cwd: Working directory for command execution

        Returns:
            Dictionary with command result
        """
        try:
            sfdk_command = self.get_sfdk_command()
            cmd = [sfdk_command] + args

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            )

            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace")

            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "output": output,
                "command": " ".join(cmd),
                "cwd": str(cwd) if cwd else None,
            }

        except Exception as e:
            logger.error(f"Error executing SFDK command: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": " ".join([self.get_sfdk_command()] + args),
            }

    async def build_project(
        self,
        project_path: Path,
        target_arch: str = "armv7hl",
        build_dir_name: str = "build_amogus",
        context: Any | None = None,
    ) -> dict[str, Any]:
        """Build project using SFDK with proper pipeline.

        Follows the correct SFDK build pipeline:
        1. Navigate to project directory
        2. Configure target (sfdk config target=...)
        3. Create build directory (../build_amogus)
        4. Execute build from build directory (sfdk build ../project_name)

        Args:
            project_path: Path to project directory
            target_arch: Target architecture
            build_dir_name: Name of build directory to create
            context: FastMCP context for real-time updates

        Returns:
            Dictionary with build result
        """
        logger.info(f"Starting SFDK build process for project: {project_path}")
        logger.info(f"Target architecture: {target_arch}")
        logger.info(f"Build directory name: {build_dir_name}")

        # Send initial progress
        if context:
            await context.info("🚀 Starting SFDK build process...")
            await context.report_progress(0, 100, "Initializing SFDK build")

        try:
            # Validate project directory exists
            if not project_path.exists():
                error_msg = f"Project directory does not exist: {project_path}"
                logger.error(error_msg)
                if context:
                    await context.error(error_msg)
                return {"success": False, "error": error_msg}

            # Get project name for build command
            project_name = self.get_project_name(project_path)
            logger.info(f"Project name: {project_name}")

            if context:
                await context.info(f"📁 Project: {project_name}")
                await context.report_progress(5, 100, "Project validation complete")

            # Step 1: Get SFDK target name (5-10%)
            if context:
                await context.info("🎯 Looking up SFDK target...")
                await context.report_progress(8, 100, "Looking up build target")

            logger.info(f"Looking up SFDK target for architecture: {target_arch}")
            target_name = await self.get_target_for_arch(target_arch)
            if not target_name:
                error_msg = f"No SFDK target found for architecture: {target_arch}"
                logger.error(error_msg)
                if context:
                    await context.error(error_msg)
                return {"success": False, "error": error_msg}

            logger.info(f"Found SFDK target: {target_name}")
            if context:
                await context.info(f"✅ Found target: {target_name}")
                await context.report_progress(
                    12, 100, f"Target selected: {target_name}"
                )

            # Step 2: Configure target from project directory (12-16%)
            if context:
                await context.info("⚙️ Configuring SFDK target...")
                await context.report_progress(14, 100, "Configuring build target")

            logger.info("Configuring SFDK target from project directory...")
            config_result = await self.execute_command_streaming(
                ["config", f"target={target_name}"],
                cwd=project_path,
                context=context,
                show_output=False,  # Don't show config output, it's not interesting
            )

            if not config_result["success"]:
                logger.warning(
                    f"Could not configure SFDK target: {config_result.get('output')}"
                )
                if context:
                    await context.warning(
                        "⚠️ Target configuration had issues, but continuing..."
                    )
            else:
                logger.info("SFDK target configured successfully")
                if context:
                    await context.info("✅ SFDK target configured successfully")

            if context:
                await context.report_progress(16, 100, "Target configuration complete")

            # Step 3: Create build directory (16-20%)
            if context:
                await context.info(f"📂 Creating build directory: {build_dir_name}")
                await context.report_progress(18, 100, "Creating build directory")

            logger.info("Creating build directory...")
            build_result = await self.create_build_directory(
                project_path, build_dir_name
            )
            if not build_result["success"]:
                error_msg = (
                    f"Failed to create build directory: {build_result.get('error')}"
                )
                if context:
                    await context.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}

            build_path = build_result["build_path"]
            logger.info(f"Build directory created: {build_path}")

            if context:
                await context.info(f"✅ Build directory ready: {build_path}")
                await context.report_progress(20, 100, "Build environment ready")

            # Step 4: Execute build from build directory (20-100%)
            if context:
                await context.info("🔨 Starting SFDK build...")
                await context.report_progress(22, 100, "Starting build process")

            build_cmd = ["build", f"../{project_name}"]
            logger.info(
                f"Executing SFDK build command from {build_path}: {' '.join(build_cmd)}"
            )

            if context:
                await context.info(f"🔧 Executing: sfdk {' '.join(build_cmd)}")

            build_exec_result = await self.execute_command_streaming(
                build_cmd,
                cwd=build_path,
                context=context,
                show_output=True,  # Show all filtered build output
            )

            # Collect all commands executed for reporting
            commands_executed = [
                f"cd {project_path}",
                f"sfdk config target={target_name}",
                f"mkdir {build_path}",
                f"cd {build_path}",
                f"sfdk {' '.join(build_cmd)}",
            ]

            if build_exec_result["success"]:
                logger.info("SFDK build command completed successfully")

                if context:
                    await context.info("🎉 Build completed successfully!")
                    await context.report_progress(100, 100, "Build complete")

                # Log full output but truncate for response
                full_output = build_exec_result["output"]
                logger.info(f"Full SFDK build output:\n{full_output}")

                # Look for RPM artifacts in both build directory and project RPMS
                if context:
                    await context.info("🔍 Searching for build artifacts...")

                logger.info("Searching for build artifacts...")
                artifacts = []

                # Check build directory for RPMs
                for rpm_file in build_path.rglob("*.rpm"):
                    if rpm_file.is_file():
                        artifacts.append(str(rpm_file))

                # Check project RPMS directory as fallback
                rpms_dir = project_path / "RPMS"
                if rpms_dir.exists():
                    for rpm_file in rpms_dir.rglob("*.rpm"):
                        if rpm_file.is_file() and str(rpm_file) not in artifacts:
                            artifacts.append(str(rpm_file))

                logger.info(f"Found {len(artifacts)} RPM artifacts")

                if context:
                    if artifacts:
                        await context.info(f"📦 Found {len(artifacts)} RPM package(s):")
                        for artifact in artifacts:
                            await context.info(f"  • {artifact}")
                    else:
                        await context.warning(
                            "⚠️ No RPM artifacts found - build may not have created packages"
                        )

                return {
                    "success": True,
                    "build_type": "sfdk",
                    "output": truncate_output(full_output),
                    "artifacts": artifacts,
                    "project_dir": str(project_path),
                    "build_dir": str(build_path),
                    "project_name": project_name,
                    "target_name": target_name,
                    "target_arch": target_arch,
                    "commands_executed": commands_executed,
                    "output_truncated": len(full_output) > 5000
                    or len(full_output.split("\n")) > 50,
                }
            else:
                error_msg = f"SFDK build failed with exit code {build_exec_result['returncode']}"
                logger.error(error_msg)

                if context:
                    await context.error(f"❌ Build failed: {error_msg}")

                # Log full output but truncate for response
                full_output = build_exec_result.get("output", "No output")
                logger.error(f"Full SFDK build output:\n{full_output}")

                return {
                    "success": False,
                    "error": error_msg,
                    "output": truncate_output(full_output),
                    "project_dir": str(project_path),
                    "build_dir": str(build_path) if "build_path" in locals() else None,
                    "project_name": project_name,
                    "target_name": target_name,
                    "target_arch": target_arch,
                    "commands_executed": commands_executed,
                    "output_truncated": len(full_output) > 5000
                    or len(full_output.split("\n")) > 50,
                }

        except Exception as e:
            error_msg = f"Error building with SFDK: {e}"
            logger.error(error_msg)
            if context:
                await context.error(f"💥 Unexpected error: {error_msg}")
            return {"success": False, "error": str(e)}

    def get_project_name(self, project_path: Path) -> str:
        """Get project name from project path.

        Args:
            project_path: Path to project directory

        Returns:
            Project directory name
        """
        return project_path.name

    async def create_build_directory(
        self, project_path: Path, build_dir_name: str = "build_amogus"
    ) -> dict[str, Any]:
        """Create build directory relative to project.

        Args:
            project_path: Path to project directory
            build_dir_name: Name of build directory to create

        Returns:
            Dictionary with creation result and build directory path
        """
        try:
            # Build directory is created as sibling to project directory
            build_path = project_path.parent / build_dir_name

            # Remove existing build directory if it exists
            if build_path.exists():
                logger.info(f"Removing existing build directory: {build_path}")
                import shutil

                shutil.rmtree(build_path)

            # Create new build directory
            logger.info(f"Creating build directory: {build_path}")
            build_path.mkdir(parents=True, exist_ok=True)

            return {
                "success": True,
                "build_path": build_path,
                "message": f"Build directory created: {build_path}",
            }

        except Exception as e:
            logger.error(f"Error creating build directory: {e}")
            return {"success": False, "error": str(e)}

    def get_info(self) -> dict[str, Any]:
        """Get SFDK wrapper information.

        Returns:
            Dictionary with wrapper configuration
        """
        return {
            "aurora_home": str(self.aurora_home),
            "sfdk_path": str(self.sfdk_path),
            "sfdk_command": self.get_sfdk_command(),
            "environment_variables": {
                "SFDK_AURORA": os.getenv("SFDK_AURORA"),
                "SFDK": os.getenv("SFDK"),
            },
        }
