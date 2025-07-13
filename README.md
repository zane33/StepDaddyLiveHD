# freesky 🚀

A self-hosted IPTV proxy built with [Reflex](https://reflex.dev), enabling you to watch over 1,000 📺 TV channels and search for live events or sports matches ⚽🏀. Stream directly in your browser 🌐 or through any media player client 🎶. You can also download the entire playlist (`playlist.m3u8`) and integrate it with platforms like Jellyfin 🍇 or other IPTV media players.

---

## ✨ Features

- **📱 Stream Anywhere**: Watch TV channels on any device via the web or media players.
- **🔎 Event Search**: Quickly find the right channel for live events or sports.
- **📄 Playlist Integration**: Download the `playlist.m3u8` and use it with Jellyfin or any IPTV client.
- **⚙️ Customizable Hosting**: Host the application locally or deploy it via Docker with various configuration options.

---

## 📦 Dependencies

freesky relies on several key Python packages, each serving a specific purpose in the application:

### Core Dependencies

- **`reflex==0.8.0`**
  - Primary web framework for building the full-stack application
  - Handles both frontend and backend, compiling Python to React
  - Provides real-time state management and WebSocket communication
  - Used for: UI components, state management, routing, and real-time updates

- **`curl-cffi==0.11.4`**
  - High-performance HTTP client with CFFI bindings
  - Supports advanced features like HTTP/2 and connection pooling
  - Used for: Fetching channel data and stream information with optimal performance

- **`httpx[http2]==0.28.1`**
  - Modern HTTP client with HTTP/2 support
  - Provides both sync and async APIs
  - Used for: Making HTTP requests to external services and handling stream proxying

### Backend Server

- **`uvicorn[standard]==0.32.1`**
  - Lightning-fast ASGI server implementation
  - Provides production-ready features with the [standard] extras
  - Used for: Serving the backend application with WebSocket support

- **`fastapi==0.115.6`**
  - Modern, fast web framework for building APIs
  - Provides automatic OpenAPI documentation
  - Used for: Backend API endpoints and WebSocket handling

### Utilities

- **`python-dateutil==2.9.0`**
  - Powerful extensions to Python's datetime module
  - Used for: Handling timestamps and schedule information

- **`aiohttp==3.10.11`**
  - Asynchronous HTTP client/server framework
  - Used for: Async HTTP requests and WebSocket communication

## 🐳 Docker Configuration

The application uses a multi-stage Docker build for optimal image size and security. Here's a breakdown of the Docker setup:

### Dockerfile Structure

```dockerfile
# Build stage
FROM python:3.13 AS builder
# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg
# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs
# Set up Python virtual environment
RUN python -m venv /app/.venv
# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
# Build frontend
COPY . .
RUN npm install && npm run build

# Runtime stage
FROM python:3.13-slim
# Install runtime dependencies
RUN apt-get update -y && apt-get install -y \
    caddy \
    redis-server
# Copy built application
COPY --from=builder /app /app
COPY --from=builder /srv /srv
# Configure entrypoint
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
```

### Docker Compose Configuration

The `docker-compose.yml` file provides a production-ready setup with:

- **Network Configuration**:
  - Exposed ports for frontend and backend
  - Internal Docker network for service communication
  - DNS configuration for reliable name resolution

- **Environment Variables**:
  - Flexible configuration through environment variables
  - Default values for quick deployment
  - Support for proxy settings

- **Resource Management**:
  - Automatic container restart
  - Network access control
  - Host machine access when needed

Example `docker-compose.yml`:
```yaml
version: '3.8'
services:
  step-daddy-live-hd:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "${PORT:-3000}:${PORT:-3000}"
      - "${BACKEND_PORT:-8005}:${BACKEND_PORT:-8005}"
      - "2019:2019"  # Caddy admin port
    environment:
      - PORT=${PORT:-3000}
      - BACKEND_PORT=${BACKEND_PORT:-8005}
      - API_URL=http://localhost:${PORT:-3000}
      - DADDYLIVE_URI=${DADDYLIVE_URI:-https://thedaddy.click}
      - PROXY_CONTENT=${PROXY_CONTENT:-TRUE}
      - SOCKS5=${SOCKS5:-}
      - WORKERS=${WORKERS:-6}
    networks:
      step-daddy-network:
        aliases:
          - step-daddy-live-hd
    restart: unless-stopped
```

---

## 🔄 Frontend-Backend Architecture

freesky uses a modern architecture built with **Reflex** (Python web framework) that provides seamless real-time communication between frontend and backend. Here's how the components interact:

### 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Caddy Proxy   │    │   Backend       │
│   (Reflex App)  │◄──►│   (Port 3000)   │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Reflex State    │    │ Static Files    │    │ IPTV Data       │
│ Management      │    │ & Routing       │    │ Processing      │
│ (Built-in WS)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🌐 Frontend Components

The frontend is built entirely with **Reflex**, a Python web framework that compiles to React, providing a responsive web interface for browsing and streaming TV channels.

#### **Key Frontend Features:**
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices
- **🔍 Real-time Search**: Live filtering of channels and events with instant updates
- **📺 Video Player**: Built-in web player with adaptive streaming
- **📊 Real-time Updates**: Live channel status and connection monitoring
- **🎯 Auto-refresh**: Automatic periodic updates with manual refresh controls
- **🔄 State Management**: Reactive state updates without page reloads

#### **Frontend Technologies:**
- **Reflex**: Full-stack Python web framework
- **Python**: All frontend logic written in Python
- **Reactive State**: Built-in state management system
- **Real-time Communication**: Native WebSocket support
- **Adaptive Video Player**: HLS/DASH streaming support
- **Responsive Design**: Mobile-first approach with CSS-in-Python

### 🔧 Backend Components

The backend is built with **FastAPI** and provides REST API endpoints for data processing and content delivery. Real-time communication is handled by Reflex's built-in WebSocket system.

#### **Key Backend Features:**
- **🚀 FastAPI**: High-performance async web framework
- **📊 Data Processing**: Channel parsing and IPTV stream handling
- **🎭 Content Proxying**: Optional video stream proxying
- **🔒 CORS Handling**: Cross-origin request management
- **⚡ Caching**: Intelligent caching for improved performance
- **🔄 Background Tasks**: Periodic channel updates and monitoring

#### **Backend Technologies:**
- **FastAPI**: Modern Python web framework for API endpoints
- **Reflex Integration**: Seamless integration with Reflex state system
- **Uvicorn**: ASGI server with multiple workers
- **Aiohttp**: Async HTTP client for external requests
- **Python 3.13**: Latest Python with async/await support

### 📡 Communication Protocols

#### **1. HTTP/REST API**
The backend exposes several REST endpoints for standard operations:

```
GET  /                          # Frontend static files (served by Caddy)
GET  /stream/<channel_id>       # Stream video content
GET  /playlist.m3u8            # Download M3U8 playlist
GET  /logo/<logo_id>           # Channel logos and images
GET  /key/<url>/<host>         # Streaming keys
GET  /content/<path>           # Proxied content
GET  /health                   # Health check endpoint
GET  /ping                     # Simple ping endpoint
```

#### **2. Reflex State Management**
Real-time features use Reflex's built-in state management system:

**Python State Updates:**
```python
class State(rx.State):
    channels: List[Channel] = []
    search_query: str = ""
    is_loading: bool = False
    connection_status: str = "connected"
    
    async def load_channels(self):
        """Load channels with real-time updates"""
        self.is_loading = True
        self.channels = backend.get_channels()
        self.is_loading = False
    
    async def search_channels(self, query: str):
        """Real-time search filtering"""
        self.search_query = query
    
    async def refresh_channels(self):
        """Manual refresh with status updates"""
        await self.load_channels()
```

**Reactive Frontend Updates:**
```python
# Real-time filtered results
@rx.var
def filtered_channels(self) -> List[Channel]:
    if not self.search_query:
        return self.channels
    return [ch for ch in self.channels 
            if self.search_query.lower() in ch.name.lower()]

# Automatic UI updates when state changes
rx.foreach(State.filtered_channels, channel_card)
```

### 🔄 Data Flow Examples

#### **1. Channel Browsing Flow**
```
1. User opens homepage
   Reflex Frontend → State.on_load() → Backend
   
2. Backend fetches channel data
   Backend → External IPTV API → Channel List
   
3. State updates automatically
   Backend → State.channels → Reactive UI Update
   
4. Frontend renders channel grid
   Reflex State → rx.foreach() → Automatic UI Rendering
```

#### **2. Real-time Search Flow**
```
1. User types in search box
   Input Field → State.search_channels() → State Update
   
2. State variable updates
   State.search_query → Reactive @rx.var → Filtered Results
   
3. UI updates automatically
   State.filtered_channels → rx.foreach() → Live UI Update
   
4. No page reload needed
   Reflex State Management → Instant Visual Feedback
```

#### **3. Video Streaming Flow**
```
With PROXY_CONTENT=TRUE:
User → Reflex Frontend → Backend → External Stream → Backend → User

With PROXY_CONTENT=FALSE:
User → Reflex Frontend → Backend → Stream URL → Frontend → External Stream
```

### 🛠️ Configuration Impact on Communication

#### **API_URL Configuration**
- **Purpose**: Defines how frontend communicates with backend
- **Local Setup**: `http://192.168.1.100:3000`
- **Production**: `https://yourdomain.com`
- **Impact**: Affects all API calls and WebSocket connections

#### **PROXY_CONTENT Configuration**
- **TRUE**: All video streams proxied through backend
  - ✅ Better CORS handling
  - ✅ Unified authentication
  - ⚠️ Higher bandwidth usage
- **FALSE**: Direct streaming from external sources
  - ✅ Lower server load
  - ❌ Potential CORS issues
  - ❌ Limited control over streams

#### **WORKERS Configuration**
- **Purpose**: Number of backend worker processes
- **Impact**: Affects concurrent user capacity
- **Recommendation**: 1 worker per 50-100 concurrent users

### 🔍 Real-time Features

#### **Live Channel Status**
- **Purpose**: Monitor channel availability and connection status
- **Technology**: Reflex state management with periodic backend updates
- **Frequency**: Every 5 minutes with manual refresh option

#### **Real-time Search**
- **Purpose**: Instant search filtering without page reloads
- **Technology**: Reactive state variables with @rx.var decorators
- **Performance**: Immediate UI updates on keystroke

#### **Auto-refresh System**
- **Purpose**: Keep channel data fresh automatically
- **Technology**: Background asyncio tasks with state updates
- **Control**: User can toggle auto-refresh on/off

### 🚨 Error Handling

#### **Connection Failures**
```python
# Reflex handles connection issues through state management
async def load_channels(self):
    self.is_loading = True
    self.connection_status = "connecting"
    
    try:
        self.channels = backend.get_channels()
        self.connection_status = "connected"
    except Exception as e:
        self.connection_status = "error"
        # Load from fallback cache
        self.channels = load_fallback_channels()
    finally:
        self.is_loading = False
```

#### **API Timeouts**
```python
# Backend implements timeout handling with fallback
@fastapi_app.get("/stream/{channel_id}")
async def stream(channel_id: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(stream_url)
            return response.content
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Stream timeout")
```

### 🔒 Security Considerations

#### **CORS Configuration**
- **Frontend Origin**: Automatically configured based on `API_URL`
- **Reflex Security**: Built-in CSRF protection and secure state management
- **API Endpoints**: CORS headers added for browser compatibility

#### **Rate Limiting**
- **Purpose**: Prevent API abuse and ensure fair usage
- **Implementation**: Per-IP rate limiting on API endpoints
- **Limits**: 100 requests per minute per IP

#### **Input Validation**
- **Search Queries**: Sanitized through Reflex state validation
- **Channel IDs**: Validated against known channel list
- **Stream URLs**: Validated before proxying
- **State Security**: Reflex prevents direct state manipulation from client

### 📊 Performance Monitoring

#### **Health Endpoints**
```
GET /health                    # Basic health check with channel count
GET /ping                     # Simple ping endpoint
```

#### **Reflex State Monitoring**
```python
# Built-in performance tracking through state variables
class State(rx.State):
    connection_status: str = "connected"
    last_update: str = ""
    channels_count: int = 0
    is_loading: bool = False
    
    @rx.var
    def status_color(self) -> str:
        """Visual indicator of system health"""
        return "green" if self.connection_status == "connected" else "red"
```

#### **Backend Performance Metrics**
- **Channel Count**: Number of available channels
- **Cache Performance**: Stream cache hit rates
- **Response Times**: Average API response times
- **Error Rates**: Failed request percentages
- **Background Tasks**: Channel update task status

This architecture ensures scalable, real-time performance using Reflex's reactive state management system, eliminating the complexity of manual WebSocket handling while providing instant UI updates.

---

## 🗺️ Site Map

### Pages Overview:

- **🏠 Home**: Browse and search for TV channels.
- **📺 Live Events**: Quickly find channels broadcasting live events and sports.
- **📥 Playlist Download**: Download the `playlist.m3u8` file for integration with media players.

---

## 📸 Screenshots

**Home Page**
<img alt="Home Page" src="https://files.catbox.moe/qlqqs5.png">

**Watch Page**
<img alt="Watch Page" src="https://files.catbox.moe/974r9w.png">

**Live Events**
<img alt="Live Events" src="https://files.catbox.moe/7oawie.png">

---

## 📚 Hosting Options

Check out the [official Reflex hosting documentation](https://reflex.dev/docs/hosting/self-hosting/) for more advanced self-hosting setups!

### 🔒 Security Configuration

For detailed security configuration and best practices, including Content Security Policy (CSP), reverse proxy setup, and network security, please refer to [SECURITY.md](SECURITY.md).

Key security features:
- Content Security Policy (CSP) configuration
- Reverse proxy security with Caddy
- CORS and WebSocket security
- Rate limiting and DDoS protection
- Development vs Production security modes