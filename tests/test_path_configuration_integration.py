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

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastmcp import Client
from aurora_mcp.server import create_server


@pytest.fixture
def temp_environment():
    """Create temporary directories and environment for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create directory structure
        aurora_home = temp_path / "aurora"
        sfdk_path = temp_path / "custom-sfdk"
        psdk_path = temp_path / "custom-psdk"

        aurora_home.mkdir()
        sfdk_path.mkdir()
        psdk_path.mkdir()

        # Create PSDK targets directory
        (psdk_path / "targets" / "AuroraOS-4.0.2.257-armv7hl").mkdir(parents=True)

        # Create fake SFDK binary
        (sfdk_path / "bin").mkdir()
        sfdk_bin = sfdk_path / "bin" / "sfdk"
        sfdk_bin.write_text("#!/bin/bash\necho 'SFDK mock version 1.0'")
        sfdk_bin.chmod(0o755)

        yield {
            "aurora_home": str(aurora_home),
            "sfdk_path": str(sfdk_path),
            "psdk_path": str(psdk_path),
            "sfdk_bin": str(sfdk_bin),
        }


@pytest.mark.asyncio
async def test_server_with_custom_paths(temp_environment):
    """Test server creation with custom SFDK/PSDK paths."""
    env_vars = {
        "SFDK_AURORA": temp_environment["sfdk_path"],
        "PSDK_AURORA": temp_environment["psdk_path"],
        "MCP_BUILD_TOOL": "auto",
    }

    with patch.dict(os.environ, env_vars):
        server = create_server(temp_environment["aurora_home"])

        async with Client(server) as client:
            # Test list_build_tools with custom paths
            result = await client.call_tool("list_build_tools")

            assert result["success"] is True
            assert "tools" in result

            # Check SFDK configuration
            sfdk_tool = next(t for t in result["tools"] if t["type"] == "sfdk")
            assert sfdk_tool["path"] == temp_environment["sfdk_path"]
            assert temp_environment["sfdk_path"] in sfdk_tool["command"]

            # Check PSDK configuration
            psdk_tool = next(t for t in result["tools"] if t["type"] == "psdk")
            assert psdk_tool["path"] == temp_environment["psdk_path"]
            assert psdk_tool["available"] is True

            # Check environment variables are reported
            assert "environment_variables" in result
            env_vars = result["environment_variables"]
            assert env_vars["SFDK_AURORA"] == temp_environment["sfdk_path"]
            assert env_vars["PSDK_AURORA"] == temp_environment["psdk_path"]


@pytest.mark.asyncio
async def test_build_tool_selection_with_custom_paths(temp_environment):
    """Test build tool selection works with custom paths."""
    env_vars = {
        "SFDK_AURORA": temp_environment["sfdk_path"],
        "PSDK_AURORA": temp_environment["psdk_path"],
        "MCP_BUILD_TOOL": "psdk",  # Force PSDK
    }

    with patch.dict(os.environ, env_vars):
        server = create_server(temp_environment["aurora_home"])

        async with Client(server) as client:
            # Test that PSDK is selected when forced
            with patch(
                "aurora_mcp.tools.qt_build_tool.QtBuildTool._build_with_psdk"
            ) as mock_build:
                mock_build.return_value = {
                    "success": True,
                    "message": "Built with PSDK",
                    "psdk_path": temp_environment["psdk_path"],
                }

                # Create a dummy project directory
                project_dir = Path(temp_environment["aurora_home"]) / "test-project"
                project_dir.mkdir()
                (project_dir / "CMakeLists.txt").write_text(
                    "cmake_minimum_required(VERSION 3.16)"
                )

                result = await client.call_tool(
                    "build_qt_project",
                    {"project_path": str(project_dir), "build_type": "Release"},
                )

                # Verify PSDK build was called
                mock_build.assert_called_once()


@pytest.mark.asyncio
async def test_generic_vs_aurora_priority(temp_environment):
    """Test that Aurora-specific environment variables take priority."""
    env_vars = {
        "SFDK_AURORA": temp_environment["sfdk_path"],
        "SFDK": "/should/not/be/used",
        "PSDK_AURORA": temp_environment["psdk_path"],
        "PSDK": "/should/not/be/used",
    }

    with patch.dict(os.environ, env_vars):
        server = create_server(temp_environment["aurora_home"])

        async with Client(server) as client:
            result = await client.call_tool("list_build_tools")

            # Verify Aurora-specific paths are used
            sfdk_tool = next(t for t in result["tools"] if t["type"] == "sfdk")
            psdk_tool = next(t for t in result["tools"] if t["type"] == "psdk")

            assert sfdk_tool["path"] == temp_environment["sfdk_path"]
            assert psdk_tool["path"] == temp_environment["psdk_path"]

            # Verify environment config shows correct priority
            env_config = result["environment_variables"]
            assert env_config["SFDK_AURORA"] == temp_environment["sfdk_path"]
            assert env_config["PSDK_AURORA"] == temp_environment["psdk_path"]
