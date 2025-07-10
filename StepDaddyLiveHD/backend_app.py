"""
Backend-only entry point for StepDaddyLiveHD.
This creates a backend app with proper Socket.IO support.
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

# Import required modules
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from StepDaddyLiveHD import backend

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
    engineio_logger=True,
    logger=True
)

# Create the main FastAPI app
app = FastAPI(
    title="StepDaddyLiveHD Backend",
    description="IPTV proxy backend with Socket.IO support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add all routes from the backend
for route in backend.fastapi_app.routes:
    app.router.routes.append(route)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Socket.IO client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Socket.IO client disconnected: {sid}")

@sio.event
async def message(sid, data):
    print(f"Received message from {sid}: {data}")
    await sio.emit('response', {'data': 'Message received'}, room=sid)

# Mount the Socket.IO app to handle /_event
socketio_app = socketio.ASGIApp(sio, app, socketio_path='/_event')

# Add the lifespan task for channel updates
@app.on_event("startup")
async def startup_event():
    """Start the channel update task on startup."""
    asyncio.create_task(backend.update_channels())

# Export the combined app
app = socketio_app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port) 