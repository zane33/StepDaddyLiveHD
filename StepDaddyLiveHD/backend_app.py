"""
Backend-only entry point for StepDaddyLiveHD.
This creates a backend app for API endpoints and WebSocket communication.
"""

import os
import sys
import uvicorn
import asyncio
import json
import logging
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
workers = int(os.environ.get("WORKERS", "3"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.ping_tasks: Dict[str, asyncio.Task] = {}
        self.last_ping: Dict[str, float] = {}
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_count += 1
        logger.info(f"WebSocket client connected. Total connections: {self.connection_count}")
        
        # Start ping task for this connection
        self.ping_tasks[client_id] = asyncio.create_task(self._ping_client(client_id))
    
    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            # Cancel ping task
            if client_id in self.ping_tasks:
                self.ping_tasks[client_id].cancel()
                del self.ping_tasks[client_id]
            
            # Remove connection
            del self.active_connections[client_id]
            self.connection_count -= 1
            logger.info(f"WebSocket client disconnected. Total connections: {self.connection_count}")
    
    async def _ping_client(self, client_id: str):
        """Send periodic pings to keep connection alive."""
        try:
            while True:
                if client_id in self.active_connections:
                    websocket = self.active_connections[client_id]
                    try:
                        await websocket.send_text("2")  # Engine.IO ping packet
                        self.last_ping[client_id] = asyncio.get_event_loop().time()
                    except Exception as e:
                        logger.error(f"Error sending ping to client {client_id}: {str(e)}")
                        await self.disconnect(client_id)
                        break
                    await asyncio.sleep(25)  # Send ping every 25 seconds
                else:
                    break
        except asyncio.CancelledError:
            pass
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {str(e)}")
                disconnected.add(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)

manager = ConnectionManager()

@app.websocket("/_event/")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(id(websocket))
    try:
        # Accept connection
        await manager.connect(websocket, client_id)
        
        # Send Engine.IO open packet
        await websocket.send_text("0{\"sid\":\"" + client_id + "\",\"upgrades\":[],\"pingInterval\":25000,\"pingTimeout\":20000}")
        
        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                
                # Handle Engine.IO packets
                if message == "2probe":  # Engine.IO probe packet
                    await websocket.send_text("3probe")  # Send probe response
                elif message == "5":  # Engine.IO upgrade packet
                    await websocket.send_text("6")  # Send upgrade confirmation
                elif message == "3":  # Engine.IO pong packet
                    manager.last_ping[client_id] = asyncio.get_event_loop().time()
                else:
                    # Handle regular messages
                    try:
                        # Parse message and broadcast state updates
                        data = json.loads(message)
                        if "event" in data:
                            await manager.broadcast(json.dumps({
                                "event": data["event"],
                                "data": data.get("data", {})
                            }))
                    except json.JSONDecodeError:
                        pass  # Ignore invalid JSON
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"Error in websocket connection {client_id}: {str(e)}")
    finally:
        await manager.disconnect(client_id)

def run():
    """Run the backend server."""
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=backend_port,
        workers=workers,
        loop="asyncio",
        ws_ping_interval=None,  # We handle pings ourselves
        ws_ping_timeout=None,
        timeout_keep_alive=30,
        backlog=2048,
        limit_concurrency=1000,
        limit_max_requests=10000,
        timeout_graceful_shutdown=10,
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    run() 