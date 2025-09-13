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
from unittest.mock import patch, AsyncMock

from aurora_mcp.tools.qt_build_tool import QtBuildTool


@pytest.fixture
def temp_aurora_home():
    """Create temporary Aurora home directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        aurora_home = Path(temp_dir) / "aurora-test"
        aurora_home.mkdir(parents=True)

        # Create PSDK directory
        (aurora_home / "psdk" / "targets" / "AuroraOS-4.0.2.257-armv7hl").mkdir(
            parents=True
        )

        yield str(aurora_home)


@pytest.fixture
def qt_tool(temp_aurora_home):
    """Create QtBuildTool instance."""
    return QtBuildTool(Path(temp_aurora_home))


@pytest.mark.asyncio
async def test_build_tool_selection_explicit_sfdk(qt_tool):
    """Test explicit SFDK selection."""
    with patch.object(qt_tool, "_check_sfdk_available", return_value=True):
        result = await qt_tool._select_build_tool("sfdk")

        assert result["success"] is True
        assert result["tool_type"] == "sfdk"
        assert "SFDK" in result["message"]


@pytest.mark.asyncio
async def test_build_tool_selection_explicit_psdk(qt_tool):
    """Test explicit PSDK selection."""
    result = await qt_tool._select_build_tool("psdk")

    assert result["success"] is True
    assert result["tool_type"] == "psdk"
    assert "PSDK" in result["message"]


@pytest.mark.asyncio
async def test_build_tool_selection_auto_detect_sfdk_preferred(qt_tool):
    """Test auto-detection prefers SFDK when available."""
    with patch.object(qt_tool, "_check_sfdk_available", return_value=True):
        result = await qt_tool._select_build_tool(None)

        assert result["success"] is True
        assert result["tool_type"] == "sfdk"
        assert "Auto-detected SFDK" in result["message"]


@pytest.mark.asyncio
async def test_build_tool_selection_auto_detect_psdk_fallback(qt_tool):
    """Test auto-detection falls back to PSDK when SFDK unavailable."""
    with patch.object(qt_tool, "_check_sfdk_available", return_value=False):
        result = await qt_tool._select_build_tool(None)

        assert result["success"] is True
        assert result["tool_type"] == "psdk"
        assert "Auto-detected PSDK" in result["message"]


@pytest.mark.asyncio
async def test_build_tool_selection_no_tools_available(qt_tool):
    """Test error when no build tools available."""
    # Remove PSDK directory
    import shutil

    shutil.rmtree(qt_tool.psdk_path)

    with patch.object(qt_tool, "_check_sfdk_available", return_value=False):
        result = await qt_tool._select_build_tool(None)

        assert result["success"] is False
        assert "No build tools available" in result["error"]


@pytest.mark.asyncio
async def test_build_tool_selection_from_environment_variable(qt_tool):
    """Test build tool selection from environment variable."""
    with patch.dict(os.environ, {"MCP_BUILD_TOOL": "psdk"}):
        result = await qt_tool._select_build_tool(None)

        assert result["success"] is True
        assert result["tool_type"] == "psdk"


@pytest.mark.asyncio
async def test_build_tool_selection_invalid_tool(qt_tool):
    """Test error for invalid build tool."""
    result = await qt_tool._select_build_tool("invalid_tool")

    assert result["success"] is False
    assert "Unknown build tool: invalid_tool" in result["error"]


@pytest.mark.asyncio
async def test_list_build_tools(qt_tool):
    """Test listing available build tools."""
    with patch.object(qt_tool, "_check_sfdk_available", return_value=True):
        result = await qt_tool.list_build_tools()

        assert result["success"] is True
        assert "tools" in result
        assert len(result["tools"]) == 2  # SFDK and PSDK

        # Check SFDK info
        sfdk_tool = next(t for t in result["tools"] if t["type"] == "sfdk")
        assert sfdk_tool["available"] is True
        assert sfdk_tool["priority"] == 1
        assert "path" in sfdk_tool
        assert "command" in sfdk_tool

        # Check PSDK info
        psdk_tool = next(t for t in result["tools"] if t["type"] == "psdk")
        assert psdk_tool["available"] is True
        assert psdk_tool["priority"] == 2
        assert "path" in psdk_tool


@pytest.mark.asyncio
async def test_custom_sfdk_path():
    """Test custom SFDK path configuration."""
    with patch.dict(os.environ, {"SFDK_AURORA": "/custom/sfdk/path"}):
        qt_tool = QtBuildTool(Path("/tmp"))
        assert qt_tool.sfdk_path == Path("/custom/sfdk/path")


@pytest.mark.asyncio
async def test_custom_psdk_path():
    """Test custom PSDK path configuration."""
    with patch.dict(os.environ, {"PSDK_AURORA": "/custom/psdk/path"}):
        qt_tool = QtBuildTool(Path("/tmp"))
        assert qt_tool.psdk_path == Path("/custom/psdk/path")


@pytest.mark.asyncio
async def test_generic_path_fallback():
    """Test generic SFDK/PSDK environment variables."""
    with patch.dict(os.environ, {"SFDK": "/usr/bin/sfdk", "PSDK": "/usr/psdk"}):
        qt_tool = QtBuildTool(Path("/tmp"))
        assert qt_tool.sfdk_path == Path("/usr/bin/sfdk")
        assert qt_tool.psdk_path == Path("/usr/psdk")


@pytest.mark.asyncio
async def test_priority_aurora_over_generic():
    """Test that Aurora-specific paths take priority over generic ones."""
    env_vars = {
        "SFDK_AURORA": "/aurora/sfdk",
        "SFDK": "/generic/sfdk",
        "PSDK_AURORA": "/aurora/psdk",
        "PSDK": "/generic/psdk",
    }
    with patch.dict(os.environ, env_vars):
        qt_tool = QtBuildTool(Path("/tmp"))
        assert qt_tool.sfdk_path == Path("/aurora/sfdk")
        assert qt_tool.psdk_path == Path("/aurora/psdk")
