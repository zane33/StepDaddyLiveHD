import os
import asyncio
import httpx
import logging
import time
from functools import lru_cache
from typing import Optional, Dict, Tuple
from StepDaddyLiveHD.step_daddy import StepDaddy, Channel
from fastapi import Response, status, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .utils import urlsafe_base64_decode
import json
from urllib.parse import urlparse, urlunparse
from collections import OrderedDict

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get environment variables
frontend_port = int(os.environ.get("PORT", "3232"))
backend_port = int(os.environ.get("BACKEND_PORT", "8005"))
api_url = os.environ.get("API_URL", f"http://localhost:{frontend_port}")  # Use frontend port for integrated API

# Parse API_URL to create WebSocket URL with backend port
parsed_url = urlparse(api_url)
ws_url = urlunparse(parsed_url._replace(netloc=f"{parsed_url.hostname}:{backend_port}"))

# Create FastAPI app with better configuration
fastapi_app = FastAPI(
    title="StepDaddyLiveHD API",
    description="IPTV proxy API",
    version="1.0.0"
)

# Add CORS middleware with consolidated settings
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for docker deployment flexibility
    allow_credentials=False,  # Can't use credentials with wildcard origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create HTTP client with optimized settings for streaming
client = httpx.AsyncClient(
    http2=True,
    timeout=httpx.Timeout(15.0, connect=5.0),  # Reasonable timeouts
    limits=httpx.Limits(
        max_keepalive_connections=50,  # Increased for better streaming
        max_connections=200,            # Increased from 75
        keepalive_expiry=60.0          # Increased from 30
    ),
    follow_redirects=True
)

step_daddy = StepDaddy()

# Use OrderedDict for LRU cache behavior
class LRUCache(OrderedDict):
    def __init__(self, maxsize=0, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if self.maxsize > 0 and len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]

# Cache with size limit and TTL optimized for streaming
stream_cache = LRUCache(maxsize=100)  # Increased for better caching
cache_ttl = 30  # 30 seconds for live streaming freshness

# Track active tasks for cleanup
active_tasks: Dict[str, asyncio.Task] = {}

# Concurrency control for streaming
_stream_semaphore = asyncio.Semaphore(10)

logger.info("Backend initialized with connection pooling")

# Start channel update task
channel_update_task = None

@fastapi_app.on_event("startup")
async def startup_event():
    global channel_update_task
    # Start the channel update background task
    channel_update_task = asyncio.create_task(update_channels())
    active_tasks["channel_update"] = channel_update_task
    logger.info("Channel update background task started")

@fastapi_app.on_event("shutdown")
async def shutdown_event():
    # Cancel all active tasks
    for task_name, task in active_tasks.items():
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Task {task_name} cancelled")
    
    # Close HTTP client
    await client.aclose()
    logger.info("HTTP client and background tasks closed")

@fastapi_app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@fastapi_app.get("/stream/{channel_id}.m3u8")
async def stream(channel_id: str):
    try:
        # Check cache first
        cache_key = f"stream_{channel_id}"
        current_time = time.time()
        
        if cache_key in stream_cache:
            cached_data, cached_time = stream_cache[cache_key]
            if current_time - cached_time < cache_ttl:
                logger.info(f"Serving cached stream for channel {channel_id}")
                return Response(
                    content=cached_data,
                    media_type="application/vnd.apple.mpegurl",
                    headers={"Content-Disposition": f"attachment; filename={channel_id}.m3u8"}
                )
        
        # Generate new stream with timeout
        try:
            stream_data = await asyncio.wait_for(
                step_daddy.stream(channel_id),
                timeout=10.0  # 10 second timeout for stream generation
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout generating stream for channel {channel_id}")
            return JSONResponse(
                content={"error": "Stream generation timeout"},
                status_code=status.HTTP_504_GATEWAY_TIMEOUT
            )
        
        # Cache the result (LRU cache handles cleanup)
        stream_cache[cache_key] = (stream_data, current_time)
        
        return Response(
            content=stream_data,
            media_type="application/vnd.apple.mpegurl",
            headers={"Content-Disposition": f"attachment; filename={channel_id}.m3u8"}
        )
    except IndexError:
        return JSONResponse(content={"error": "Stream not found"}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error streaming channel {channel_id}: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@fastapi_app.get("/key/{url}/{host}")
async def key(url: str, host: str):
    try:
        # Add timeout to key retrieval
        key_data = await asyncio.wait_for(
            step_daddy.key(url, host),
            timeout=5.0  # 5 second timeout for key retrieval
        )
        return Response(
            content=key_data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=key"}
        )
    except asyncio.TimeoutError:
        logger.error(f"Timeout getting key for {url}")
        return JSONResponse(
            content={"error": "Key retrieval timeout"},
            status_code=status.HTTP_504_GATEWAY_TIMEOUT
        )
    except Exception as e:
        logger.error(f"Error getting key: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@fastapi_app.get("/content/{path}")
async def content(path: str):
    try:
        async with _stream_semaphore:  # Control concurrent streams
            async def proxy_stream():
                async with client.stream("GET", step_daddy.content_url(path), timeout=30) as response:
                    async for chunk in response.aiter_bytes(chunk_size=4 * 1024):  # Optimized chunks for lower latency
                        yield chunk
            return StreamingResponse(
                proxy_stream(), 
                media_type="application/octet-stream",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Accept-Ranges": "bytes",
                    "Transfer-Encoding": "chunked"
                }
            )
    except Exception as e:
        logger.error(f"Error proxying content: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

async def update_channels():
    update_interval = 300  # 5 minutes
    retry_interval = 60   # 1 minute on failure
    max_retries = 3      # Maximum number of retries
    
    while True:
        try:
            logger.info("Loading channels...")
            retries = 0
            success = False
            
            while not success and retries < max_retries:
                try:
                    await step_daddy.load_channels()
                    if step_daddy.channels:
                        success = True
                        logger.info(f"Successfully loaded {len(step_daddy.channels)} channels")
                        # Clear stream cache when channels are updated
                        stream_cache.clear()
                        await asyncio.sleep(update_interval)
                    else:
                        raise Exception("No channels loaded from primary source")
                except Exception as e:
                    retries += 1
                    logger.error(f"Error loading channels (attempt {retries}/{max_retries}): {str(e)}")
                    if retries < max_retries:
                        await asyncio.sleep(retry_interval)
            
            if not success:
                # All retries failed, try fallback
                if os.path.exists("StepDaddyLiveHD/fallback_channels.json"):
                    logger.info("Loading channels from fallback file...")
                    with open("StepDaddyLiveHD/fallback_channels.json", "r") as f:
                        fallback_data = json.load(f)
                        step_daddy.channels = [Channel(**channel_data) for channel_data in fallback_data]
                    if step_daddy.channels:
                        logger.info(f"Loaded {len(step_daddy.channels)} channels from fallback")
                    else:
                        logger.error("No channels in fallback file")
                else:
                    logger.error("No fallback file available")
                
                # Wait before next attempt even if using fallback
                await asyncio.sleep(update_interval)
                
        except asyncio.CancelledError:
            logger.info("Channel update task cancelled")
            break
        except Exception as e:
            logger.error(f"Unexpected error in channel update loop: {str(e)}")
            await asyncio.sleep(retry_interval)

def get_channels():
    """Get current channels with fallback handling."""
    try:
        logger.debug("Attempting to get channels from step_daddy instance")
        channels = step_daddy.channels
        if channels:
            logger.info(f"Successfully retrieved {len(channels)} channels")
            return channels
        
        logger.warning("No channels available from primary source, trying fallback")
        # Try loading from fallback synchronously if no channels available
        if os.path.exists("StepDaddyLiveHD/fallback_channels.json"):
            with open("StepDaddyLiveHD/fallback_channels.json", "r") as f:
                fallback_data = json.load(f)
                channels = [Channel(**channel_data) for channel_data in fallback_data]
            logger.info(f"Loaded {len(channels)} channels from fallback in get_channels()")
            return channels
        else:
            logger.error("No fallback channels file found")
            return []
    except Exception as e:
        logger.error(f"Error in get_channels(): {str(e)}", exc_info=True)
        return []

def get_channel(channel_id) -> Optional[Channel]:
    if not channel_id or channel_id == "":
        return None
    channels = get_channels()  # Use get_channels() to ensure fallback handling
    return next((channel for channel in channels if channel.id == channel_id), None)

@fastapi_app.get("/playlist.m3u8")
def playlist():
    return Response(
        content=step_daddy.playlist(), 
        media_type="application/vnd.apple.mpegurl", 
        headers={
            "Content-Disposition": "attachment; filename=playlist.m3u8",
            "Cache-Control": "public, max-age=300"
        }
    )

@fastapi_app.get("/api/playlist.m3u8")
def api_playlist():
    return Response(
        content=step_daddy.playlist(), 
        media_type="application/vnd.apple.mpegurl", 
        headers={
            "Content-Disposition": "attachment; filename=playlist.m3u8",
            "Cache-Control": "public, max-age=300"
        }
    )

async def get_schedule():
    return await step_daddy.schedule()

@fastapi_app.get("/logo/{logo}")
async def logo(logo: str):
    url = urlsafe_base64_decode(logo)
    file = url.split("/")[-1]
    if not os.path.exists("./logo-cache"):
        os.makedirs("./logo-cache")
    if os.path.exists(f"./logo-cache/{file}"):
        return FileResponse(
            f"./logo-cache/{file}",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
        )
    try:
        response = await client.get(
            url, 
            headers={"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"}
        )
        if response.status_code == 200:
            with open(f"./logo-cache/{file}", "wb") as f:
                f.write(response.content)
            return FileResponse(
                f"./logo-cache/{file}",
                headers={"Cache-Control": "public, max-age=86400"}
            )
        else:
            return JSONResponse(content={"error": "Logo not found"}, status_code=status.HTTP_404_NOT_FOUND)
    except httpx.ConnectTimeout:
        return JSONResponse(content={"error": "Request timed out"}, status_code=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception as e:
        logger.error(f"Error fetching logo: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@fastapi_app.get("/ping")
async def ping():
    return {"status": "ok", "channels_count": len(step_daddy.channels)}

@fastapi_app.get("/health")
async def health():
    return {
        "status": "healthy",
        "channels_count": len(step_daddy.channels),
        "cache_size": len(stream_cache),
        "uptime": time.time()
    }

@fastapi_app.get("/channels")
async def channels_endpoint():
    """Get all channels as JSON."""
    try:
        channels = get_channels()
        return {
            "channels": [
                {
                    "id": ch.id,
                    "name": ch.name,
                    "logo": ch.logo,
                    "tags": ch.tags
                }
                for ch in channels
            ],
            "count": len(channels)
        }
    except Exception as e:
        logger.error(f"Error in channels endpoint: {str(e)}")
        return {"error": str(e), "channels": [], "count": 0}

@fastapi_app.get("/schedule")
async def schedule_endpoint():
    """Get schedule data as JSON."""
    try:
        schedule_data = await get_schedule()
        return {"schedule": schedule_data, "status": "success"}
    except Exception as e:
        logger.error(f"Error in schedule endpoint: {str(e)}")
        # Return fallback schedule data
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        
        now = datetime.now(ZoneInfo("UTC"))
        fallback_schedule = {}
        
        for day_offset in range(7):  # 7 days
            day = now + timedelta(days=day_offset)
            day_key = day.strftime("%d/%m/%Y - %A")
            fallback_schedule[day_key] = {
                "Sports": [
                    {
                        "event": f"Sports Event {i+1}",
                        "time": f"{9+i*3}:00",
                        "channels": [{"channel_name": "ESPN", "channel_id": "1"}]
                    }
                    for i in range(3)
                ],
                "News": [
                    {
                        "event": f"News Hour {i+1}",
                        "time": f"{10+i*4}:00",
                        "channels": [{"channel_name": "CNN", "channel_id": "2"}]
                    }
                    for i in range(3)
                ],
                "Entertainment": [
                    {
                        "event": f"Entertainment Show {i+1}",
                        "time": f"{20+i}:00",
                        "channels": [{"channel_name": "HBO", "channel_id": "3"}]
                    }
                    for i in range(3)
                ]
            }
        
        return {"schedule": fallback_schedule, "status": "fallback"}

