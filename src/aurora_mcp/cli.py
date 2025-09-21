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

import argparse
import asyncio
import logging
import os
import sys

from aurora_mcp.server import create_server


def main():
    """Main entry point for Aurora MCP CLI."""
    parser = argparse.ArgumentParser(
        description="Aurora MCP - Aurora OS development tools MCP server"
    )

    parser.add_argument(
        "--aurora-home",
        type=str,
        default=os.getenv("AURORA_MCP_HOME", "~/AuroraOS"),
        help="Aurora OS development environment home directory",
    )

    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol to use (stdio for Claude Code, http for web access)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run MCP server on (only for http transport)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind MCP server to (only for http transport)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("AURORA_MCP_LOG_LEVEL", "INFO"),
        help="Logging level",
    )

    parser.add_argument("--version", action="version", version="Aurora MCP 0.1.0")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Aurora MCP server...")
    logger.info(f"Aurora home: {args.aurora_home}")
    logger.info(f"Transport: {args.transport}")

    if args.transport == "http":
        logger.info(f"Server: {args.host}:{args.port}")

    # Log configuration
    sfdk_path = os.getenv("SFDK_AURORA") or os.getenv("SFDK")
    psdk_path = os.getenv("PSDK_AURORA") or os.getenv("PSDK")
    build_tool = os.getenv("MCP_BUILD_TOOL", "auto-detect")

    if sfdk_path:
        logger.info(f"SFDK path: {sfdk_path}")
    if psdk_path:
        logger.info(f"PSDK path: {psdk_path}")
    logger.info(f"Build tool preference: {build_tool}")

    # Create and run server
    try:
        server = create_server(args.aurora_home)

        if args.transport == "stdio":
            # STDIO transport - no host/port needed
            asyncio.run(server.run())
        else:  # http transport
            # HTTP transport - use host and port
            asyncio.run(server.run(transport="http", host=args.host, port=args.port))

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
