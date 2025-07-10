"""
Backend-only entry point for StepDaddyLiveHD.
This creates a backend app that accepts WebSocket connections without complex protocols.
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
    description="IPTV proxy backend with minimal WebSocket support",
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

# Minimal WebSocket endpoint that just accepts and maintains connections
@app.websocket("/_event")
async def websocket_event_endpoint(websocket: WebSocket):
    """Handle WebSocket connections at /_event path."""
    try:
        await websocket.accept()
        print(f"WebSocket accepted: {websocket.client}")
        
        # Send Engine.IO handshake immediately upon connection
        try:
            handshake = '0{"sid":"mock_session","upgrades":[],"pingInterval":25000,"pingTimeout":60000}'
            await websocket.send_text(handshake)
            print(f"Sent Engine.IO handshake: {handshake}")
        except Exception as e:
            print(f"Failed to send handshake: {e}")
            return
        
        # Log any messages received from the client after handshake
        try:
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                    print(f"Received after handshake: {data}")
                    # Respond to ping/pong
                    if data == "2":
                        await websocket.send_text("3")
                        print("Sent pong")
                    elif data.startswith("40"):
                        await websocket.send_text("40")
                        print("Sent Socket.IO ack")
                    elif data.startswith("42"):
                        await websocket.send_text("42[\"message received\"]")
                        print("Sent Socket.IO message ack")
                    else:
                        await websocket.send_text(data)
                        print(f"Echoed: {data}")
                except asyncio.TimeoutError:
                    await websocket.send_text("2")
                    print("Sent keepalive ping")
        except asyncio.CancelledError:
            pass
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {websocket.client}")
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.websocket("/_event/")
async def websocket_event_slash_endpoint(websocket: WebSocket):
    """Handle WebSocket connections at /_event/ path."""
    try:
        await websocket.accept()
        print(f"WebSocket accepted (with slash): {websocket.client}")
        
        # Send Engine.IO handshake immediately upon connection
        try:
            handshake = '0{"sid":"mock_session","upgrades":[],"pingInterval":25000,"pingTimeout":60000}'
            await websocket.send_text(handshake)
            print(f"Sent Engine.IO handshake (with slash): {handshake}")
        except Exception as e:
            print(f"Failed to send handshake (with slash): {e}")
            return
        
        # Log any messages received from the client after handshake
        try:
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                    print(f"Received after handshake (with slash): {data}")
                    # Respond to ping/pong
                    if data == "2":
                        await websocket.send_text("3")
                        print("Sent pong (with slash)")
                    elif data.startswith("40"):
                        await websocket.send_text("40")
                        print("Sent Socket.IO ack (with slash)")
                    elif data.startswith("42"):
                        await websocket.send_text("42[\"message received\"]")
                        print("Sent Socket.IO message ack (with slash)")
                    else:
                        await websocket.send_text(data)
                        print(f"Echoed (with slash): {data}")
                except asyncio.TimeoutError:
                    await websocket.send_text("2")
                    print("Sent keepalive ping (with slash)")
        except asyncio.CancelledError:
            pass
    except WebSocketDisconnect:
        print(f"WebSocket disconnected (with slash): {websocket.client}")
    except Exception as e:
        print(f"WebSocket error (with slash): {e}")

# Handle parameterized paths as well
@app.websocket("/_event/{path:path}")  
async def websocket_event_path_endpoint(websocket: WebSocket, path: str):
    """Handle WebSocket connections at /_event/* paths."""
    try:
        await websocket.accept()
        print(f"WebSocket accepted on path '{path}': {websocket.client}")
        
        # Send Engine.IO handshake immediately upon connection
        try:
            handshake = '0{"sid":"mock_session","upgrades":[],"pingInterval":25000,"pingTimeout":60000}'
            await websocket.send_text(handshake)
            print(f"Sent Engine.IO handshake on '{path}': {handshake}")
        except Exception as e:
            print(f"Failed to send handshake on '{path}': {e}")
            return
        
        # Keep the connection alive and handle any messages
        try:
            while True:
                try:
                    # Try to receive messages with a timeout
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    print(f"Received on '{path}': {data}")
                    
                    # Respond to ping/pong
                    if data == "2":  # ping
                        await websocket.send_text("3")  # pong
                        print(f"Sent pong on '{path}'")
                    elif data.startswith("40"):  # Socket.IO connect
                        await websocket.send_text("40")  # ack
                        print(f"Sent Socket.IO ack on '{path}'")
                    else:
                        # Echo back any other message
                        await websocket.send_text(data)
                        print(f"Echoed on '{path}': {data}")
                        
                except asyncio.TimeoutError:
                    # Send periodic ping to keep alive
                    await websocket.send_text("2")
                    print(f"Sent keepalive ping on '{path}'")
                    
        except asyncio.CancelledError:
            pass
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected from path '{path}': {websocket.client}")
    except Exception as e:
        print(f"WebSocket error on path '{path}': {e}")

# Add the lifespan task for channel updates
@app.on_event("startup")
async def startup_event():
    """Start the channel update task on startup."""
    asyncio.create_task(backend.update_channels())

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port) 