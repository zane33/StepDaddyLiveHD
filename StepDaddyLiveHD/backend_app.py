"""
Backend-only entry point for StepDaddyLiveHD.
This runs the full Reflex app in production mode to include WebSocket endpoints.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for production mode
os.environ["REFLEX_ENV"] = "prod"

# Import the full Reflex app
from StepDaddyLiveHD.StepDaddyLiveHD import app as reflex_app
from StepDaddyLiveHD import backend

# Get the FastAPI app from the Reflex app (includes WebSocket endpoints)
app = reflex_app.api

# Add the lifespan task for channel updates
@app.on_event("startup")
async def startup_event():
    """Start the channel update task on startup."""
    asyncio.create_task(backend.update_channels())

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port) 