"""
Backend-only entry point for StepDaddyLiveHD.
This avoids frontend compilation issues in production.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables to prevent frontend compilation at runtime
os.environ["REFLEX_ENV"] = "prod"
os.environ["REFLEX_FRONTEND_ONLY"] = "true"
os.environ["REFLEX_NO_COMPILE"] = "true"

# Import only the backend, avoiding any Reflex app imports
from StepDaddyLiveHD import backend

# Create a FastAPI app from the backend
app = backend.fastapi_app

# Add the lifespan task for channel updates
@app.on_event("startup")
async def startup_event():
    """Start the channel update task on startup."""
    asyncio.create_task(backend.update_channels())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 