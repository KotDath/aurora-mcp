use rmcp::{
    ErrorData as McpError, RoleServer, ServerHandler,
    handler::server::{
        router::tool::ToolRouter,
        wrapper::Parameters,
    },
    model::*,
    schemars::JsonSchema,
    service::RequestContext,
    tool, tool_handler, tool_router,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use chrono;

/// Batch greeting request structure
#[derive(Debug, Deserialize, Serialize, JsonSchema)]
pub struct BatchGreetingRequest {
    /// List of names to greet
    #[schemars(description = "List of names to generate greetings for")]
    pub names: Vec<String>,

    /// Optional prefix for all greetings
    #[schemars(description = "Optional prefix to add before each greeting")]
    pub prefix: Option<String>,

    /// Whether to include line numbers
    #[schemars(description = "Whether to include line numbers before each greeting")]
    pub include_numbers: Option<bool>,

    /// Whether to return result as JSON
    #[schemars(description = "Whether to format the output as JSON")]
    pub as_json: Option<bool>,
}

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

    #[tool(description = "Возвращает нынешнего президента США")]
    async fn get_usa_president(&self) -> Result<CallToolResult, McpError> {
        let greeting = "В 2025 году президентом США является Дональд Трамп или Агент Краснов";

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
            "transports": ["stdio", "http", "sse"],
            "tools": [
                "hello_world() - Returns a greeting message from Aurora OS",
                "get_usa_president() - Return current usa president",
                "get_server_info() - Returns detailed server information",
                "health_check() - Returns server health status",
                "batch_greeting() - Generate personalized greetings for multiple names"
            ],
            "capabilities": [
                "tools",
                "stdio transport",
                "http transport",
                "sse transport"
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
            "transport_mode": "multi-mode (stdio/http/sse)",
            "tools_available": 4
        });

        tracing::info!("Health check requested");

        Ok(CallToolResult::success(vec![Content::text(health.to_string())]))
    }

    /// Batch Greeting Tool
    ///
    /// Generates personalized greetings for multiple names with optional formatting.
    /// This tool demonstrates how to handle complex input parameters and structured output.
    #[tool(description = "Generate personalized greetings for multiple names with customizable formatting")]
    fn batch_greeting(
        &self,
        Parameters(BatchGreetingRequest {
            names,
            prefix,
            include_numbers,
            as_json,
        }): Parameters<BatchGreetingRequest>,
    ) -> Result<CallToolResult, McpError> {
        tracing::info!("Batch greeting tool called with {} names", names.len());

        // Validate input
        if names.is_empty() {
            return Ok(CallToolResult::error(vec![Content::text(
                "Error: At least one name must be provided".to_string(),
            )]));
        }

        // Set defaults
        let prefix = prefix.unwrap_or_else(|| "Hello".to_string());
        let include_numbers = include_numbers.unwrap_or(false);
        let as_json = as_json.unwrap_or(false);

        // Generate greetings
        let mut greetings = Vec::new();
        for (i, name) in names.iter().enumerate() {
            let mut greeting = if include_numbers {
                format!("{}. {}", i + 1, prefix)
            } else {
                prefix.clone()
            };
            greeting.push_str(", ");
            greeting.push_str(name);
            greeting.push('!');

            greetings.push(greeting);
        }

        // Format output
        let result = if as_json {
            let json_result = json!({
                "greetings": greetings,
                "count": greetings.len(),
                "prefix": prefix,
                "include_numbers": include_numbers
            });
            json_result.to_string()
        } else {
            greetings.join("\n")
        };

        tracing::info!("Generated {} greetings successfully", greetings.len());

        Ok(CallToolResult::success(vec![Content::text(result)]))
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
                • get_server_info: Returns detailed server information\n\
                • health_check: Returns server health status\n\
                • batch_greeting: Generate personalized greetings for multiple names\n\n\
                Available Transports:\n\
                • stdio: Standard MCP communication mode\n\
                • http: REST API mode with JSON-RPC endpoint\n\
                • sse: Real-time Server-Sent Events mode\n\n\
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
                • get_server_info: Returns detailed server information\n\
                • health_check: Returns server health status\n\
                • batch_greeting: Generate personalized greetings for multiple names\n\n\
                Available Transports:\n\
                • stdio: Standard MCP communication mode\n\
                • http: REST API mode with JSON-RPC endpoint\n\
                • sse: Real-time Server-Sent Events mode\n\n\
                This server showcases basic MCP tool implementation using the Rust SDK \
                and demonstrates how Aurora OS can integrate with AI assistants through \
                the Model Context Protocol."
                .to_string()
            ),
        })
    }
}