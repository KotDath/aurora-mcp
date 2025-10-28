use anyhow::Result;
use clap::Parser;
use rmcp::{ServiceExt, transport::stdio};
use rmcp::transport::streamable_http_server::{StreamableHttpService, session::local::LocalSessionManager};
use tracing_subscriber::{self, EnvFilter};
use std::net::SocketAddr;
use tower_http::cors::{CorsLayer, Any};
use chrono;

mod aurora_server;

/// Command line arguments for Aurora MCP Server
#[derive(Parser, Debug)]
#[command(
    name = "aurora-mcp",
    version = env!("CARGO_PKG_VERSION"),
    about = "Aurora OS MCP Server - Demo implementation with hello world tool",
    long_about = "A Model Context Protocol (MCP) server for Aurora OS that can run in both STDIO and HTTP modes. Supports tools for greetings and server information."
)]
struct Args {
    /// Transport mode: stdio or http
    #[arg(
        short = 't',
        long = "transport",
        default_value = "stdio",
        help = "Transport mode to use for MCP communication"
    )]
    transport: TransportMode,

    /// Host address for HTTP mode (only used with --transport http)
    #[arg(
        short = 'H',
        long = "host",
        default_value = "127.0.0.1",
        help = "Host address to bind HTTP server to"
    )]
    host: String,

    /// Port for HTTP mode (only used with --transport http)
    #[arg(
        short = 'p',
        long = "port",
        default_value = "3000",
        help = "Port to bind HTTP server to"
    )]
    port: u16,

    /// Enable CORS for HTTP mode (only used with --transport http)
    #[arg(
        long = "cors",
        help = "Enable Cross-Origin Resource Sharing for HTTP mode"
    )]
    cors: bool,

    /// Log level
    #[arg(
        short = 'l',
        long = "log-level",
        default_value = "info",
        help = "Set the logging level"
    )]
    log_level: String,
}

#[derive(clap::ValueEnum, Debug, Clone)]
enum TransportMode {
    /// Use STDIO transport (default MCP mode)
    Stdio,
    /// Use HTTP transport (REST API mode)
    Http,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // Initialize the tracing subscriber with configurable log level
    let log_level = match args.log_level.to_lowercase().as_str() {
        "trace" => tracing::Level::TRACE,
        "debug" => tracing::Level::DEBUG,
        "info" => tracing::Level::INFO,
        "warn" => tracing::Level::WARN,
        "error" => tracing::Level::ERROR,
        _ => tracing::Level::INFO,
    };

    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive(log_level.into()))
        .with_writer(std::io::stderr)
        .with_ansi(false)
        .init();

    tracing::info!("Starting Aurora OS MCP Demo Server v{}", env!("CARGO_PKG_VERSION"));
    tracing::info!("Transport mode: {:?}", args.transport);

    // Create an instance of our Aurora server
    let server = aurora_server::AuroraServer::new();

    match args.transport {
        TransportMode::Stdio => {
            tracing::info!("Starting STDIO transport mode");
            let service = server.serve(stdio()).await.inspect_err(|e| {
                tracing::error!("Failed to start STDIO server: {:?}", e);
            })?;

            tracing::info!("Aurora MCP Server is running in STDIO mode and waiting for connections");
            service.waiting().await?;
        }
        TransportMode::Http => {
            let addr: SocketAddr = format!("{}:{}", args.host, args.port).parse()
                .map_err(|e| anyhow::anyhow!("Invalid address {}: {}", args.host, e))?;

            tracing::info!("Starting HTTP transport mode on {}", addr);

            // Create the HTTP service using StreamableHttpService
            let http_service = StreamableHttpService::new(
                move || Ok(server.clone()),
                LocalSessionManager::default().into(),
                Default::default(),
            );

            // Create Axum router with optional CORS
            let mut router = axum::Router::new().nest_service("/mcp", http_service);

            if args.cors {
                tracing::info!("CORS enabled for HTTP mode");
                router = router.layer(
                    CorsLayer::new()
                        .allow_origin(Any)
                        .allow_methods(Any)
                        .allow_headers(Any)
                );
            }

            // Add health check endpoint
            router = router.route("/health", axum::routing::get(health_check_handler));

            // Bind and serve
            let tcp_listener = tokio::net::TcpListener::bind(addr).await
                .map_err(|e| anyhow::anyhow!("Failed to bind to {}: {}", addr, e))?;

            tracing::info!("Aurora MCP Server is running in HTTP mode on http://{}", addr);
            tracing::info!("Available endpoints:");
            tracing::info!("  POST http://{}/mcp  - MCP JSON-RPC endpoint", addr);
            tracing::info!("  GET  http://{}/health - Health check endpoint", addr);
            tracing::info!("Press Ctrl+C to stop the server");

            let _ = axum::serve(tcp_listener, router)
                .with_graceful_shutdown(async {
                    tokio::signal::ctrl_c().await
                        .expect("Failed to listen for ctrl+c signal");
                    tracing::info!("Received shutdown signal");
                })
                .await;
        }
    }

    tracing::info!("Aurora MCP Server shutdown complete");
    Ok(())
}

/// Health check handler for HTTP mode
async fn health_check_handler() -> axum::response::Json<serde_json::Value> {
    let health = serde_json::json!({
        "status": "healthy",
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "server": "Aurora OS MCP Demo Server",
        "version": env!("CARGO_PKG_VERSION"),
        "transport_mode": "http",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health"
        }
    });

    axum::response::Json(health)
}