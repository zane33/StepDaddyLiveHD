"""
Backend-only entry point for StepDaddyLiveHD.
This creates a backend app for API endpoints only.
Real-time communication is handled by Reflex's built-in WebSocket system.
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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from StepDaddyLiveHD import backend

# Create the main FastAPI app
app = FastAPI(
    title="StepDaddyLiveHD Backend",
    description="Backend API for StepDaddyLiveHD",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        api_url,  # Frontend URL from environment
        "http://localhost:3232",     # Local development
        "http://127.0.0.1:3232",    # Alternative local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include all the backend routes
app.mount("/", backend.fastapi_app)

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "channels_count": len(backend.step_daddy.channels),
        "message": "Backend API is running. Real-time features handled by Reflex."
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 