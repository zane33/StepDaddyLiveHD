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

# Create Socket.IO server with custom path to match frontend expectations
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
    path='/_event'
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
    """Handle client connections."""
    print(f"Client connected: {sid}")
    await sio.emit('status', {'msg': 'Connected to StepDaddyLiveHD backend'}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnections."""
    print(f"Client disconnected: {sid}")

@sio.event
async def message(sid, data):
    """Handle messages from clients."""
    print(f"Message from {sid}: {data}")
    await sio.emit('response', {'msg': f'Received: {data}'}, room=sid)

@sio.event
async def ping(sid):
    """Handle ping from clients."""
    print(f"Ping from {sid}")
    await sio.emit('pong', room=sid)

# Create ASGI app that combines FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Add the lifespan task for channel updates
@app.on_event("startup")
async def startup_event():
    """Start the channel update task on startup."""
    asyncio.create_task(backend.update_channels())

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    uvicorn.run(socket_app, host="0.0.0.0", port=port) 