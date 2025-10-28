use std::time::Duration;
use std::net::SocketAddr;

use anyhow::Result;
use axum::{
    Router,
    response::Json,
    routing::get,
};
use rmcp::transport::sse_server::{SseServer, SseServerConfig};
use tokio_util::sync::CancellationToken;
use tracing::{error, info};

use crate::aurora_server::AuroraServer;

/// Health check handler for SSE mode
async fn sse_health_check() -> Json<serde_json::Value> {
    let health = serde_json::json!({
        "status": "healthy",
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "server": "Aurora OS MCP Demo Server",
        "version": env!("CARGO_PKG_VERSION"),
        "transport_mode": "sse",
        "endpoints": {
            "sse": "/sse",
            "message": "/message",
            "health": "/health"
        }
    });

    Json(health)
}

/// Create and configure SSE server with AuroraServer
pub async fn create_sse_server(
    server: AuroraServer,
    addr: SocketAddr,
    enable_cors: bool,
) -> Result<()> {
    info!("Starting SSE transport mode on {}", addr);

    // Create cancellation token for graceful shutdown
    let ct = CancellationToken::new();

    // Create SSE server configuration
    let sse_config = SseServerConfig {
        bind: addr,
        sse_path: "/sse".to_string(),
        post_path: "/message".to_string(),
        ct: ct.clone(),
        sse_keep_alive: Some(Duration::from_secs(15)),
    };

    // Create SSE server and router
    let (sse_server, sse_router) = SseServer::new(sse_config);

    // Create main router with health check endpoint
    let mut router = Router::new()
        .route("/health", get(sse_health_check))
        .merge(sse_router);

    // Add CORS if enabled
    if enable_cors {
        info!("CORS enabled for SSE mode");
        router = router.layer(
            tower_http::cors::CorsLayer::new()
                .allow_origin(tower_http::cors::Any)
                .allow_methods(tower_http::cors::Any)
                .allow_headers(tower_http::cors::Any)
        );
    }

    // Start the server
    let listener = tokio::net::TcpListener::bind(addr).await
        .map_err(|e| anyhow::anyhow!("Failed to bind to {}: {}", addr, e))?;

    let cancel_token = ct.clone();

    // Handle graceful shutdown
    tokio::spawn(async move {
        match tokio::signal::ctrl_c().await {
            Ok(()) => {
                info!("Received Ctrl+C, shutting down SSE server...");
                cancel_token.cancel();
            }
            Err(err) => {
                error!("Unable to listen for Ctrl+C signal: {}", err);
            }
        }
    });

    // Register the AuroraServer service with SSE transport
    sse_server.with_service(move || server.clone());

    info!("Aurora MCP Server is running in SSE mode on http://{}", addr);
    info!("Available endpoints:");
    info!("  GET  http://{}/sse     - SSE endpoint for server events", addr);
    info!("  POST http://{}/message - POST endpoint for client messages (with sessionId)", addr);
    info!("  GET  http://{}/health  - Health check endpoint", addr);
    info!("Press Ctrl+C to stop the server");

    // Start serving with graceful shutdown
    let server_future = axum::serve(listener, router)
        .with_graceful_shutdown(async move {
            ct.cancelled().await;
            info!("SSE server is shutting down...");
        });

    if let Err(e) = server_future.await {
        error!("SSE server error: {}", e);
        return Err(anyhow::anyhow!("SSE server failed: {}", e));
    }

    info!("SSE server has been shut down");
    Ok(())
}