"""
Backend-only entry point for StepDaddyLiveHD.
This creates a backend app for API endpoints and WebSocket communication.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for production mode
os.environ["REFLEX_ENV"] = "prod"

# Get environment variables
api_url = os.environ.get("API_URL", "http://192.168.4.5:3232")

# Import required modules
import reflex as rx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.StepDaddyLiveHD import State

# Initialize the Reflex app with WebSocket support
app = rx.App(state=State)

# Get the FastAPI app instance from Reflex
fastapi_app = app.api.fastapi_app

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        api_url,  # Frontend URL from environment
        "http://localhost:3232",     # Local development
        "http://127.0.0.1:3232",    # Alternative local
        "*",  # Allow all origins for WebSocket
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include all the backend routes
fastapi_app.mount("/api", backend.fastapi_app)

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
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", 8000))
    # Start the Reflex app with WebSocket support
    app.compile()
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        ws="websockets",  # Enable WebSocket support
        ws_ping_interval=20,  # Keep connections alive
        ws_ping_timeout=30,
        log_level="info"
    ) 