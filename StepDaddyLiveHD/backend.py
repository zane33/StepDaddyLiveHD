import os
import asyncio
import httpx
import logging
import time
from functools import lru_cache
from typing import Optional
from StepDaddyLiveHD.step_daddy import StepDaddy, Channel
from fastapi import Response, status, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .utils import urlsafe_base64_decode
import json
from urllib.parse import urlparse, urlunparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
api_url = os.environ.get("API_URL", "http://localhost:3232")
backend_port = int(os.environ.get("BACKEND_PORT", "8005"))

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
    allow_origins=[
        api_url,  # Frontend URL from environment
        ws_url,   # WebSocket URL with backend port
        "http://0.0.0.0:3232",     # Local development frontend
        f"http://0.0.0.0:{backend_port}",  # Local development backend
        "http://127.0.0.1:3232",    # Alternative local frontend
        f"http://127.0.0.1:{backend_port}",  # Alternative local backend
        "*",  # Allow all origins for WebSocket
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create HTTP client with connection pooling
client = httpx.AsyncClient(
    http2=True,
    timeout=httpx.Timeout(30.0, connect=10.0),
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0
    ),
    follow_redirects=True
)

step_daddy = StepDaddy()

# Cache for expensive operations
stream_cache = {}
cache_ttl = 300  # 5 minutes

logger.info("Backend initialized with connection pooling")

# Start channel update task
channel_update_task = None

@fastapi_app.on_event("startup")
async def startup_event():
    global channel_update_task
    # Start the channel update background task
    channel_update_task = asyncio.create_task(update_channels())
    logger.info("Channel update background task started")

@fastapi_app.on_event("shutdown")
async def shutdown_event():
    global channel_update_task
    # Cancel the channel update task
    if channel_update_task:
        channel_update_task.cancel()
        try:
            await channel_update_task
        except asyncio.CancelledError:
            pass
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
        
        # Generate new stream
        stream_data = await step_daddy.stream(channel_id)
        
        # Cache the result
        stream_cache[cache_key] = (stream_data, current_time)
        
        # Clean old cache entries
        if len(stream_cache) > 100:  # Limit cache size
            oldest_key = min(stream_cache.keys(), key=lambda k: stream_cache[k][1])
            del stream_cache[oldest_key]
        
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
        return Response(
            content=await step_daddy.key(url, host),
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=key"}
        )
    except Exception as e:
        logger.error(f"Error getting key: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@fastapi_app.get("/content/{path}")
async def content(path: str):
    try:
        async def proxy_stream():
            async with client.stream("GET", step_daddy.content_url(path), timeout=60) as response:
                async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                    yield chunk
        return StreamingResponse(
            proxy_stream(), 
            media_type="application/octet-stream",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    except Exception as e:
        logger.error(f"Error proxying content: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

async def update_channels():
    while True:
        try:
            logger.info("Loading channels...")
            await step_daddy.load_channels()
            
            # Verify channels were actually loaded
            if not step_daddy.channels:
                raise Exception("No channels loaded from primary source")
                
            logger.info(f"Successfully loaded {len(step_daddy.channels)} channels")
            # Clear stream cache when channels are updated
            stream_cache.clear()
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            logger.info("Channel update task cancelled")
            break
        except Exception as e:
            logger.error(f"Error loading channels: {str(e)}")
            # Try to load from fallback if available
            try:
                if os.path.exists("StepDaddyLiveHD/fallback_channels.json"):
                    logger.info("Loading channels from fallback file...")
                    with open("StepDaddyLiveHD/fallback_channels.json", "r") as f:
                        fallback_data = json.load(f)
                        step_daddy.channels = [Channel(**channel_data) for channel_data in fallback_data]
                    if not step_daddy.channels:
                        raise Exception("No channels loaded from fallback")
                    logger.info(f"Loaded {len(step_daddy.channels)} channels from fallback")
                else:
                    logger.error("No fallback file found at StepDaddyLiveHD/fallback_channels.json")
            except Exception as fallback_error:
                logger.error(f"Fallback loading also failed: {str(fallback_error)}")
            # Continue running but wait a bit longer before retrying
            await asyncio.sleep(60)  # Wait 1 minute before retrying on initial load, 10 minutes on subsequent failures

@lru_cache(maxsize=1)
def get_channels():
    """Get current channels with fallback handling."""
    channels = step_daddy.channels
    if not channels:
        # Try loading from fallback synchronously if no channels available
        try:
            if os.path.exists("StepDaddyLiveHD/fallback_channels.json"):
                with open("StepDaddyLiveHD/fallback_channels.json", "r") as f:
                    fallback_data = json.load(f)
                    channels = [Channel(**channel_data) for channel_data in fallback_data]
                logger.info(f"Loaded {len(channels)} channels from fallback in get_channels()")
        except Exception as e:
            logger.error(f"Error loading fallback in get_channels(): {str(e)}")
    return channels

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

