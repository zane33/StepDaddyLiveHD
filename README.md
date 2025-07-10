# StepDaddyLiveHD 🚀

A self-hosted IPTV proxy built with [Reflex](https://reflex.dev), enabling you to watch over 1,000 📺 TV channels and search for live events or sports matches ⚽🏀. Stream directly in your browser 🌐 or through any media player client 🎶. You can also download the entire playlist (`playlist.m3u8`) and integrate it with platforms like Jellyfin 🍇 or other IPTV media players.

---

## ✨ Features

- **📱 Stream Anywhere**: Watch TV channels on any device via the web or media players.
- **🔎 Event Search**: Quickly find the right channel for live events or sports.
- **📄 Playlist Integration**: Download the `playlist.m3u8` and use it with Jellyfin or any IPTV client.
- **⚙️ Customizable Hosting**: Host the application locally or deploy it via Docker with various configuration options.

---

## 🐳 Docker Installation (Recommended)

> ⚠️ **Important:** If you plan to use this application across your local network (LAN), you must set `API_URL` to the **local IP address** of the device hosting the server in `.env`.

### Option 1: Docker Compose (Command Line)
1. Make sure you have Docker and Docker Compose installed on your system.
2. Clone the repository and navigate into the project directory:
3. Run the following command to start the application:
   ```bash
   docker compose up -d
   ```

### Option 2: Plain Docker (Command Line)
```bash
docker build -t step-daddy-live-hd .
docker run -p 3232:3232 step-daddy-live-hd
```

### Option 3: Portainer Deployment (Recommended for GUI Users)

Portainer provides a user-friendly web interface for managing Docker containers. Here's how to deploy StepDaddyLiveHD using Portainer:

#### **🚀 Method 1: Git Repository Deployment (Best Practice)**

1. **Access Portainer**
   - Open your Portainer web interface (usually `http://your-server:9000`)
   - Navigate to **Stacks** → **Add Stack**

2. **Configure Stack**
   - **Name**: `stepdaddylivehd` (or your preferred name)
   - **Build method**: Select **Repository**
   - **Repository URL**: `https://github.com/zane33/StepDaddyLiveHD.git`
   - **Repository reference**: `main` (or your preferred branch)
   - **Repository authentication**: Leave empty (public repo)

3. **Compose File Configuration**
   - **Web editor**: Select this option
   - **Compose path**: `docker-compose.yml`
   - Paste the following compose configuration:

```yaml
version: '3.8'

services:
  step-daddy-live-hd:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3232:3232"
    environment:
      - PORT=3232
      - API_URL=${API_URL:-http://localhost:3232}
      - BACKEND_HOST_URI=${BACKEND_HOST_URI:-}
      - DADDYLIVE_URI=${DADDYLIVE_URI:-https://thedaddy.click}
      - PROXY_CONTENT=${PROXY_CONTENT:-TRUE}
      - SOCKS5=${SOCKS5:-}
      - WORKERS=${WORKERS:-4}
    restart: unless-stopped
    env_file:
      - .env
```

4. **Environment Variables (Optional)**
   - Click **Advanced mode** to add environment variables
   - Add any custom values you need:
     ```
     API_URL=http://192.168.1.100:3232
     WORKERS=6
     PROXY_CONTENT=TRUE
     ```

5. **Deploy**
   - Click **Deploy the stack**
   - Portainer will clone the repository and build the container

#### **📁 Method 2: Upload Files**

1. **Prepare Files**
   - Download the repository as ZIP from GitHub
   - Extract to a folder on your local machine

2. **Upload to Portainer**
   - In Portainer, go to **Stacks** → **Add Stack**
   - **Build method**: Select **Upload**
   - **Upload path**: Select the extracted folder
   - **Compose path**: `docker-compose.yml`

3. **Deploy**
   - Click **Deploy the stack**

#### **🔧 Method 3: Custom Configuration**

For advanced users who want full control:

1. **Create Custom Compose File**
   ```yaml
   version: '3.8'
   
   services:
     stepdaddylivehd:
       build:
         context: .
         dockerfile: Dockerfile
       ports:
         - "3232:3232"
       environment:
         - PORT=3232
         - API_URL=http://192.168.1.100:3232
         - DADDYLIVE_URI=https://thedaddy.click
         - PROXY_CONTENT=TRUE
         - WORKERS=6
       restart: unless-stopped
       container_name: stepdaddylivehd
   ```

2. **Deploy in Portainer**
   - Use **Web editor** method
   - Paste your custom configuration
   - Deploy

#### **⚙️ Portainer-Specific Tips**

**Resource Allocation:**
- **Memory**: Minimum 512MB, Recommended 1GB
- **CPU**: 1-2 cores for basic usage, 4+ cores for high traffic
- **Storage**: 2-5GB for the container and cache

**Network Configuration:**
- **Port**: 3232 (default) - change if needed
- **Network Mode**: Bridge (default)
- **Publish Ports**: `3232:3232`

**Environment Variables in Portainer:**
- Use the **Environment** tab in stack configuration
- Variables are applied at build time
- Changes require stack redeployment

**Monitoring:**
- **Logs**: View real-time logs in Portainer
- **Stats**: Monitor CPU, memory, and network usage
- **Health Checks**: Built-in health endpoint at `/health`

**Troubleshooting:**
- **Build Failures**: Check logs for dependency issues
- **Port Conflicts**: Change port in compose file
- **Permission Issues**: Ensure proper file permissions
- **Network Issues**: Verify firewall settings

#### **🔄 Updating in Portainer**

1. **Automatic Updates** (if using Git method):
   - Go to **Stacks** → Your stack
   - Click **Pull and redeploy**
   - Portainer will pull latest changes and rebuild

2. **Manual Updates**:
   - Download new repository version
   - Upload and redeploy stack
   - Or edit compose file in web editor

#### **📊 Performance Optimization**

**For High Traffic:**
```yaml
services:
  stepdaddylivehd:
    # ... other config ...
    environment:
      - WORKERS=8
      - PROXY_CONTENT=TRUE
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
```

**For Low Resource Systems:**
```yaml
services:
  stepdaddylivehd:
    # ... other config ...
    environment:
      - WORKERS=2
      - PROXY_CONTENT=FALSE
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

---

## 🖥️ Local Installation

1. Install Python 🐍 (tested with version 3.12).
2. Clone the repository and navigate into the project directory:
   ```bash
   git clone https://github.com/gookie-dev/StepDaddyLiveHD
   cd step-daddy-live-hd
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Initialize Reflex:
   ```bash
   reflex init
   ```
6. Run the application in production mode:
   ```bash
   reflex run --env prod
   ```

---

## ⚙️ Configuration

### Environment Variables

StepDaddyLiveHD uses several environment variables to configure its behavior. Here's a detailed explanation of each:

#### **🌐 Network & Server Configuration**

- **`PORT`** (default: `3232`)
  - **Purpose**: Sets the port number that Caddy (the reverse proxy) listens on
  - **Usage**: Change this if port 3232 is already in use on your system
  - **Example**: `PORT=8080` to run on port 8080

- **`API_URL`** (optional)
  - **Purpose**: Sets the public URL where your server is accessible
  - **When Required**: 
    - For LAN access: Set to your local IP (e.g., `http://192.168.1.100:3232`)
    - For internet access: Set to your domain (e.g., `https://yourdomain.com`)
  - **Impact**: Affects how URLs are generated in playlists and web interface
  - **Example**: `API_URL=https://iptv.yourdomain.com`

- **`BACKEND_HOST_URI`** (optional)
  - **Purpose**: Configures a custom backend host URI for advanced setups
  - **Use Cases**:
    - Load balancing with multiple backend instances
    - Custom backend domain/subdomain
    - Reverse proxy configurations
  - **Example**: `BACKEND_HOST_URI=http://backend.yourdomain.com:8000`

#### **📺 Content & Streaming Configuration**

- **`DADDYLIVE_URI`** (default: `https://thedaddy.click`)
  - **Purpose**: Sets the endpoint URI for the daddylive service
  - **Use Cases**:
    - Point to alternative daddylive servers
    - Use custom daddylive instances
    - Backup/mirror servers
  - **Example**: `DADDYLIVE_URI=https://custom-daddylive.example.com`

- **`PROXY_CONTENT`** (default: `TRUE`)
  - **Purpose**: Controls whether video content is proxied through your server
  - **When `TRUE`** (recommended for web usage):
    - ✅ Web players work without CORS issues
    - ✅ Original video URLs are hidden from clients
    - ✅ Better privacy and control
    - ⚠️ Higher server bandwidth usage
  - **When `FALSE`** (for external players only):
    - ✅ Lower server load and bandwidth usage
    - ❌ Web players may not work due to CORS
    - ❌ Original URLs are exposed to clients
  - **Example**: `PROXY_CONTENT=FALSE` for VLC/MPV only usage

#### **🚀 Performance Configuration**

- **`WORKERS`** (default: `4`)
  - **Purpose**: Sets the number of worker processes for handling concurrent requests
  - **Recommendations**:
    - **Development**: `WORKERS=1`
    - **Production**: `WORKERS=4` (default)
    - **High Traffic**: `WORKERS=8` or higher
  - **Impact**: More workers = better concurrent handling but higher resource usage
  - **Example**: `WORKERS=8` for high-traffic deployments

#### **🔒 Network & Security Configuration**

- **`SOCKS5`** (optional)
  - **Purpose**: Routes all daddylive traffic through a SOCKS5 proxy
  - **Use Cases**:
    - Bypass regional restrictions
    - Enhanced privacy
    - Network routing requirements
  - **Format**: `host:port` or `user:password@host:port`
  - **Example**: `SOCKS5=127.0.0.1:1080` or `SOCKS5=user:pass@proxy.example.com:1080`

### Configuration Examples

#### **🏠 Basic Home Setup**
```bash
# Simple local setup
PORT=3232
API_URL=http://192.168.1.100:3232
PROXY_CONTENT=TRUE
WORKERS=4
```

#### **🌍 Internet-Facing Server**
```bash
# Production setup with domain
PORT=3232
API_URL=https://iptv.yourdomain.com
PROXY_CONTENT=TRUE
WORKERS=6
```

#### **🎯 High-Performance Deployment**
```bash
# Optimized for high traffic
PORT=3232
API_URL=https://iptv.yourdomain.com
BACKEND_HOST_URI=http://backend.yourdomain.com:8000
PROXY_CONTENT=TRUE
WORKERS=8
```

#### **🔒 Privacy-Focused Setup**
```bash
# With SOCKS5 proxy for enhanced privacy
PORT=3232
API_URL=https://iptv.yourdomain.com
PROXY_CONTENT=TRUE
WORKERS=4
SOCKS5=user:password@proxy.example.com:1080
```

#### **📱 External Players Only**
```bash
# Optimized for VLC/MPV usage (lower server load)
PORT=3232
API_URL=https://iptv.yourdomain.com
PROXY_CONTENT=FALSE
WORKERS=2
```

### 🔧 Common Configuration Issues

#### **Web Player Not Working**
- **Problem**: CORS errors or video not loading
- **Solution**: Ensure `PROXY_CONTENT=TRUE` is set
- **Alternative**: Use external players like VLC/MPV

#### **Can't Access from Other Devices**
- **Problem**: Only accessible from localhost
- **Solution**: Set `API_URL` to your local IP address
- **Example**: `API_URL=http://192.168.1.100:3232`

#### **High Server Load**
- **Problem**: Server becomes slow with multiple users
- **Solutions**:
  - Increase `WORKERS` (try 6-8)
  - Set `PROXY_CONTENT=FALSE` if using external players only
  - Monitor system resources

#### **Playlist URLs Not Working**
- **Problem**: Playlist links point to wrong address
- **Solution**: Ensure `API_URL` is set correctly
- **Check**: URLs in `/playlist.m3u8` should match your server

#### **SOCKS5 Proxy Issues**
- **Problem**: Connection failures with proxy
- **Solutions**:
  - Verify proxy server is running
  - Check credentials format: `user:password@host:port`
  - Test proxy connectivity separately

### Performance Features

- **Multi-Worker Support**: Configurable worker processes for better concurrent handling
- **Connection Pooling**: Efficient HTTP connection management
- **Caching**: Stream and logo caching for improved performance
- **Rate Limiting**: Built-in protection against overwhelming requests
- **Health Monitoring**: Real-time health checks and performance metrics

### Environment Variable Examples

**Basic Configuration:**
```bash
PORT=3232
API_URL=http://localhost:3232
PROXY_CONTENT=TRUE
WORKERS=4
```

**Advanced Configuration with Custom Endpoints:**
```bash
PORT=3232
API_URL=https://your-domain.com
BACKEND_HOST_URI=http://backend.your-domain.com:8000
DADDYLIVE_URI=https://custom-daddylive.example.com
PROXY_CONTENT=TRUE
WORKERS=8
SOCKS5=127.0.0.1:1080
```

**High-Performance Configuration:**
```bash
PORT=3232
API_URL=https://your-domain.com
WORKERS=8
PROXY_CONTENT=TRUE
```

### Example Docker Command
```bash
# Basic setup
docker build -t step-daddy-live-hd .
docker run -p 3232:3232 step-daddy-live-hd

# Advanced setup with all options
docker build \
  --build-arg PORT=3232 \
  --build-arg API_URL=https://iptv.yourdomain.com \
  --build-arg BACKEND_HOST_URI=http://backend.yourdomain.com:8000 \
  --build-arg DADDYLIVE_URI=https://thedaddy.click \
  --build-arg PROXY_CONTENT=TRUE \
  --build-arg WORKERS=8 \
  --build-arg SOCKS5=user:password@proxy.example.com:1080 \
  -t step-daddy-live-hd .

docker run \
  -e PORT=3232 \
  -e API_URL=https://iptv.yourdomain.com \
  -e BACKEND_HOST_URI=http://backend.yourdomain.com:8000 \
  -e DADDYLIVE_URI=https://thedaddy.click \
  -e PROXY_CONTENT=TRUE \
  -e WORKERS=8 \
  -e SOCKS5=user:password@proxy.example.com:1080 \
  -p 3232:3232 \
  step-daddy-live-hd

# Minimal setup for external players only
docker run \
  -e PORT=3232 \
  -e API_URL=http://192.168.1.100:3232 \
  -e PROXY_CONTENT=FALSE \
  -e WORKERS=2 \
  -p 3232:3232 \
  step-daddy-live-hd
```

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