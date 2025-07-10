"""
Backend-only entry point for StepDaddyLiveHD.
This creates a backend app for API endpoints and WebSocket communication.
"""

import os
import sys
import uvicorn
from pathlib import Path
from urllib.parse import urlparse, urlunparse

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for production mode
os.environ["REFLEX_ENV"] = "prod"
os.environ["REFLEX_SKIP_COMPILE"] = "1"  # Skip frontend compilation in production

# Get environment variables
api_url = os.environ.get("API_URL", "http://192.168.4.5:3232")
backend_port = int(os.environ.get("BACKEND_PORT", "8005"))  # Match frontend default

# Parse API_URL to create WebSocket URL with backend port
parsed_url = urlparse(api_url)
ws_url = urlunparse(parsed_url._replace(netloc=f"{parsed_url.hostname}:{backend_port}"))

# Import required modules
import reflex as rx
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.StepDaddyLiveHD import State

# Initialize the Reflex app with WebSocket support
app = rx.App(_state=State)

# Create a new FastAPI app
fastapi_app = FastAPI()

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        api_url,  # Frontend URL from environment
        ws_url,   # WebSocket URL with backend port
        "http://localhost:3232",     # Local development frontend
        f"http://localhost:{backend_port}",  # Local development backend
        "http://127.0.0.1:3232",    # Alternative local frontend
        f"http://127.0.0.1:{backend_port}",  # Alternative local backend
        "*",  # Allow all origins for WebSocket
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create a middleware to handle both Reflex and backend routes
@fastapi_app.middleware("http")
async def route_middleware(request: Request, call_next):
    # Strip /api prefix if present
    path = request.url.path
    if path.startswith("/api"):
        path = path[4:]  # Remove /api prefix
        request.scope["path"] = path
    
    # Forward to backend app
    response = await backend.fastapi_app(request.scope, request.receive, request.send)
    return response

# Mount the Reflex app for WebSocket events
fastapi_app.mount("/_event", app._api)

# Health check endpoint
@fastapi_app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "channels_count": len(backend.step_daddy.channels),
        "message": "Backend API is running with Reflex WebSocket support."
    }

if __name__ == "__main__":
    # Start the Reflex app with WebSocket support
    # Skip compilation in production/container environments
    if not os.environ.get("REFLEX_SKIP_COMPILE"):
        app._compile()
    
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=backend_port,  # Use the same backend_port as frontend config
        ws="websockets",  # Enable WebSocket support
        ws_ping_interval=20,  # Keep connections alive
        ws_ping_timeout=30,
        log_level="info"
    ) 