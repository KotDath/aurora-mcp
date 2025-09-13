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

import pytest
import tempfile
from pathlib import Path

from fastmcp import Client
from aurora_mcp.server import create_server


@pytest.fixture
def temp_aurora_home():
    """Create temporary Aurora home directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        aurora_home = Path(temp_dir) / "aurora-test"
        aurora_home.mkdir(parents=True)
        
        # Create basic directory structure
        (aurora_home / "psdk").mkdir()
        (aurora_home / "projects").mkdir()
        (aurora_home / "templates").mkdir()
        
        yield str(aurora_home)


@pytest.fixture
def aurora_server(temp_aurora_home):
    """Create Aurora MCP server for testing."""
    return create_server(temp_aurora_home)


@pytest.mark.asyncio
async def test_server_info(aurora_server):
    """Test getting server information."""
    async with Client(aurora_server) as client:
        result = await client.call_tool("aurora_mcp_info")
        
        assert result is not None
        assert "server" in result
        assert result["server"] == "Aurora MCP"
        assert "version" in result
        assert "available_tools" in result


@pytest.mark.asyncio
async def test_check_environment(aurora_server):
    """Test environment checking."""
    async with Client(aurora_server) as client:
        result = await client.call_tool("check_aurora_environment")
        
        assert result is not None
        assert "psdk_available" in result
        assert "projects_dir" in result


@pytest.mark.asyncio
async def test_qt_build_targets(aurora_server):
    """Test listing Qt build targets."""
    async with Client(aurora_server) as client:
        result = await client.call_tool("list_qt_targets")
        
        assert result is not None
        assert "success" in result
        assert "targets" in result


@pytest.mark.asyncio
async def test_list_templates(aurora_server):
    """Test listing available templates."""
    async with Client(aurora_server) as client:
        result = await client.call_tool("list_available_templates")
        
        assert result is not None
        assert "success" in result
        assert "templates" in result