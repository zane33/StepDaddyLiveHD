"""
Backend-only entry point for StepDaddyLiveHD.
This creates a simple backend app that handles WebSocket connections.
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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from StepDaddyLiveHD import backend

# Create the main FastAPI app
app = FastAPI(
    title="StepDaddyLiveHD Backend",
    description="IPTV proxy backend with WebSocket support",
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

# Add WebSocket endpoints to handle /_event connections (match the frontend pattern)
@app.websocket("/_event/")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        print(f"WebSocket connected: {websocket.client}")
        
        # Keep the connection alive and handle Engine.IO-style messages
        while True:
            try:
                # Wait for messages from the client
                data = await websocket.receive_text()
                print(f"Received WebSocket message: {data}")
                
                # Send a simple acknowledgment
                await websocket.send_text("40")  # Engine.IO message type for connection
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected: {websocket.client}")
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

# Also handle the parameterized version
@app.websocket("/_event/{path:path}")
async def websocket_endpoint_with_params(websocket: WebSocket, path: str):
    try:
        await websocket.accept()
        print(f"WebSocket connected with path {path}: {websocket.client}")
        
        # Keep the connection alive
        while True:
            try:
                # Wait for messages from the client
                data = await websocket.receive_text()
                print(f"Received WebSocket message on {path}: {data}")
                
                # Send a simple acknowledgment
                await websocket.send_text("40")  # Engine.IO message type for connection
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected from {path}: {websocket.client}")
                break
                
    except Exception as e:
        print(f"WebSocket error on {path}: {e}")
        try:
            await websocket.close()
        except:
            pass

# Add the lifespan task for channel updates
@app.on_event("startup")
async def startup_event():
    """Start the channel update task on startup."""
    asyncio.create_task(backend.update_channels())

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port) 