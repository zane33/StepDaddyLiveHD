"""
Reflex configuration for StepDaddyLiveHD.
"""
import os
import reflex as rx

# Get environment variables with defaults
api_url = os.environ.get("API_URL", "http://192.168.4.5:3232")
backend_port = int(os.environ.get("BACKEND_PORT", "8005"))

# Create config
config = rx.Config(
    app_name="StepDaddyLiveHD",
    api_url=api_url,
    backend_port=backend_port,
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
)
