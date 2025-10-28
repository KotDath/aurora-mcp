use rmcp::{
    ErrorData as McpError, RoleServer, ServerHandler,
    handler::server::{
        router::tool::ToolRouter,
    },
    model::*,
    service::RequestContext,
    tool, tool_handler, tool_router,
};
use serde_json::json;
use chrono;

#[derive(Clone)]
pub struct AuroraServer {
    tool_router: ToolRouter<AuroraServer>,
}

#[tool_router]
impl AuroraServer {
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self {
            tool_router: Self::tool_router(),
        }
    }

    /// Hello World Tool - Returns a greeting message from Aurora OS
    ///
    /// This is the main demonstration tool that returns a simple "hello world"
    /// message from the Aurora OS MCP server. It serves as a basic example of
    /// how to implement MCP tools using the Rust SDK macros.
    #[tool(description = "Returns a hello world greeting from Aurora OS MCP Server")]
    async fn hello_world(&self) -> Result<CallToolResult, McpError> {
        let greeting = "Hello, World! from Aurora OS MCP Server 🌟";

        tracing::info!("Hello world tool called, returning: {}", greeting);

        Ok(CallToolResult::success(vec![Content::text(greeting)]))
    }

    /// Get Server Information Tool
    ///
    /// Returns detailed information about the Aurora OS MCP server including
    /// version, capabilities, and available tools.
    #[tool(description = "Get detailed information about the Aurora OS MCP server")]
    fn get_server_info(&self) -> Result<CallToolResult, McpError> {
        let info = json!({
            "server": "Aurora OS MCP Demo Server",
            "version": "0.1.0",
            "description": "A demonstration MCP server for Aurora OS integration",
            "platform": "Aurora OS",
            "protocol_version": "2024-11-05",
            "transports": ["stdio", "http"],
            "tools": [
                "hello_world() - Returns a greeting message from Aurora OS",
                "get_server_info() - Returns detailed server information",
                "health_check() - Returns server health status"
            ],
            "capabilities": [
                "tools",
                "stdio transport",
                "http transport"
            ]
        });

        tracing::info!("Server info requested");

        Ok(CallToolResult::success(vec![Content::text(info.to_string())]))
    }

    /// Health Check Tool
    ///
    /// Returns the current health status of the Aurora OS MCP server.
    /// Useful for monitoring and HTTP mode health checks.
    #[tool(description = "Check the health status of the Aurora OS MCP server")]
    fn health_check(&self) -> Result<CallToolResult, McpError> {
        let health = json!({
            "status": "healthy",
            "timestamp": chrono::Utc::now().to_rfc3339(),
            "server": "Aurora OS MCP Demo Server",
            "version": "0.1.0",
            "uptime_seconds": 0, // TODO: Implement actual uptime tracking
            "transport_mode": "multi-mode (stdio/http)",
            "tools_available": 3
        });

        tracing::info!("Health check requested");

        Ok(CallToolResult::success(vec![Content::text(health.to_string())]))
    }
}

#[tool_handler]
impl ServerHandler for AuroraServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .build(),
            server_info: Implementation::from_build_env(),
            instructions: Some(
                "Aurora OS MCP Demo Server\n\n\
                This is a demonstration MCP (Model Context Protocol) server designed \
                specifically for Aurora OS integration.\n\n\
                Available Tools:\n\
                • hello_world: Returns a greeting message from Aurora OS\n\
                • get_server_info: Returns detailed server information\n\n\
                This server showcases basic MCP tool implementation using the Rust SDK \
                and demonstrates how Aurora OS can integrate with AI assistants through \
                the Model Context Protocol."
                .to_string()
            ),
        }
    }

    async fn initialize(
        &self,
        _request: InitializeRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<InitializeResult, McpError> {
        tracing::info!("Aurora OS MCP Server initialized by client");

        Ok(InitializeResult {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .build(),
            server_info: Implementation::from_build_env(),
            instructions: Some(
                "Aurora OS MCP Demo Server\n\n\
                This is a demonstration MCP (Model Context Protocol) server designed \
                specifically for Aurora OS integration.\n\n\
                Available Tools:\n\
                • hello_world: Returns a greeting message from Aurora OS\n\
                • get_server_info: Returns detailed server information\n\n\
                This server showcases basic MCP tool implementation using the Rust SDK \
                and demonstrates how Aurora OS can integrate with AI assistants through \
                the Model Context Protocol."
                .to_string()
            ),
        })
    }
}