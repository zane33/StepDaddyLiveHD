"""
Backend-only entry point for StepDaddyLiveHD.
This creates a backend app for API endpoints and WebSocket communication.
"""

import os
import sys
import uvicorn
from pathlib import Path
from urllib.parse import urlparse

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for production mode
os.environ["REFLEX_ENV"] = "prod"
os.environ["REFLEX_SKIP_COMPILE"] = "1"  # Skip frontend compilation in production

# Get environment variables
api_url = os.environ.get("API_URL", "http://localhost:3232")  # Frontend interface
backend_uri = os.environ.get("BACKEND_URI", "http://localhost:8005")  # Backend service
backend_port = int(os.environ.get("BACKEND_PORT", "8005"))

# Create WebSocket URL from API_URL (where clients will connect)
ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")

# Import required modules
import reflex as rx
from fastapi import FastAPI, Request, WebSocket, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse, JSONResponse
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.StepDaddyLiveHD import State
from starlette.types import ASGIApp

# Initialize the Reflex app with WebSocket support
app = rx.App(_state=State)

# Create a new FastAPI app
fastapi_app = FastAPI()

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        api_url,       # Frontend interface
        ws_url,        # WebSocket URL
        backend_uri,   # Backend service
        "*",          # Allow all origins for WebSocket
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Health check endpoint - must be before the middleware
@fastapi_app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "channels_count": len(backend.step_daddy.channels),
        "message": "Backend API is running with Reflex WebSocket support."
    }

# Create a middleware to handle both Reflex and backend routes
@fastapi_app.middleware("http")
async def route_middleware(request: Request, call_next):
    # Strip /api prefix if present
    path = request.url.path
    if path.startswith("/api"):
        path = path[4:]  # Remove /api prefix
        request.scope["path"] = path
    
    # Forward to backend app
    return await call_next(request)

# Create backend routes
@fastapi_app.get("/stream/{channel_id}.m3u8")
async def stream(channel_id: str):
    return await backend.stream(channel_id)

@fastapi_app.get("/key/{url}/{host}")
async def key(url: str, host: str):
    return await backend.key(url, host)

@fastapi_app.get("/content/{path}")
async def content(path: str):
    return await backend.content(path)

@fastapi_app.get("/playlist.m3u8")
def playlist():
    return backend.playlist()

@fastapi_app.get("/logo/{logo}")
async def logo(logo: str):
    return await backend.logo(logo)

# Mount the Reflex app for WebSocket events - must be after all routes
if app._api is not None:
    fastapi_app.mount("", app._api)  # Mount at root to handle all WebSocket events

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
        log_level="info",
        http="h11"  # Force HTTP/1.1 for WebSocket support
    ) 