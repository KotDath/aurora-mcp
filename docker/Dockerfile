# Copyright 2025 Daniil Markevich (KotDath)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Aurora MCP Server Docker Image
FROM python:3.12-slim

# Install system dependencies for Aurora OS development
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    bzip2 \
    build-essential \
    cmake \
    qtbase5-dev \
    qtchooser \
    qt5-qmake \
    qtbase5-dev-tools \
    rpm \
    rpmbuild \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install UV package manager
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY tests/ ./tests/

# Install Python dependencies
RUN uv sync

# Create Aurora OS development directories
RUN mkdir -p /opt/aurora-os/{psdk,build-engine,projects}

# Set environment variables
ENV PYTHONPATH=/app/src
ENV AURORA_MCP_HOME=/opt/aurora-os
ENV PATH="/app/.venv/bin:$PATH"

# Expose MCP server port
EXPOSE 8000

# Default command to run the Aurora MCP server
CMD ["uv", "run", "python", "-m", "aurora_mcp.server"]