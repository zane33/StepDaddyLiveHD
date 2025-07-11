"""
Reflex configuration for StepDaddyLiveHD.
"""
import os
import reflex as rx

# Get environment variables with defaults
frontend_port = int(os.environ.get("PORT", "3232"))
backend_port = int(os.environ.get("BACKEND_PORT", "8005"))
api_url = os.environ.get("API_URL", f"http://localhost:{frontend_port}")  # Frontend interface
backend_uri = os.environ.get("BACKEND_URI", f"http://localhost:{backend_port}")  # Backend service
daddylive_uri = os.environ.get("DADDYLIVE_URI", "https://thedaddy.click")
proxy_content = os.environ.get("PROXY_CONTENT", "TRUE").lower() == "true"
socks5 = os.environ.get("SOCKS5", "")

# Create config
config = rx.Config(
    app_name="StepDaddyLiveHD",
    api_url=api_url,  # Frontend interface where clients connect
    backend_port=backend_port,  # Internal backend port
    env=rx.Env.PROD,  # Use production mode
    frontend_packages=[
        "socket.io-client",
        "@emotion/react",
        "@emotion/styled",
        "@mui/material",
        "@mui/icons-material",
    ],
    # Enable WebSocket support
    connect_on_init=True,  # Connect WebSocket on page load
    timeout=30000,  # WebSocket timeout in milliseconds
    # Allow all origins for WebSocket
    cors_allowed_origins=["*"],
    # Custom configuration
    daddylive_uri=daddylive_uri,
    proxy_content=proxy_content,
    socks5=socks5,
)
