# Troubleshooting Guide

## Common Issues and Solutions

### 1. Connection Refused Error (Port 8005)

**Error**: `dial tcp 127.0.0.1:8005: connect: connection refused`

**Cause**: The backend is not running on port 8005 as expected by Caddy.

**Solutions**:
- Check if the container is running: `docker ps`
- Check container logs: `docker logs <container_name>`
- Verify the backend started properly by looking for "Backend initialized" in logs
- Test the backend directly: `curl http://localhost:8005/ping`

### 2. Curl Error in Channel Loading

**Error**: `curl_cffi.requests.exceptions.HTTPError: Failed to perform, curl: (16)`

**Cause**: Network connectivity issues or external API being unavailable.

**Solutions**:
- Check internet connectivity from within the container
- Verify the external API is accessible: `curl https://thedaddy.click/24-7-channels.php`
- Check if SOCKS5 proxy is configured correctly (if using)
- The app will now use fallback channels if the external API fails

### 3. Backend Not Starting

**Symptoms**: No backend logs, connection refused errors

**Solutions**:
- Check if all required files are present
- Verify Python dependencies are installed
- Check if the startup script has execute permissions
- Look for any Python import errors in logs

### 4. Poor Performance with Multiple Connections

**Symptoms**: Slow response times, timeouts, connection errors under load

**Causes**:
- Single-threaded backend
- No connection pooling
- No caching
- Resource limitations

**Solutions**:
- Increase `WORKERS` environment variable (default: 6, recommended: 4-8)
- Monitor system resources (CPU, memory)
- Check cache hit rates using `/health` endpoint
- Use the performance monitoring script: `python monitor_performance.py http://localhost:${PORT:-3000}`

## Performance Optimizations

### Environment Variables for Performance

To check current environment variables in a running container:
```bash
docker exec <container_name> env | grep -E "(PORT|API_URL|DADDYLIVE_URI|PROXY_CONTENT|SOCKS5|WORKERS|BACKEND_PORT)"
```

### Core Variables

- `PORT`: The frontend port (default: 3000)
- `BACKEND_PORT`: The backend service port (default: 8005)
- `BACKEND_URI`: The backend URI without port i.e. localhost or ip address
- `API_URL`: The public URL for accessing the service
- `DADDYLIVE_URI`: The daddylive service endpoint
- `PROXY_CONTENT`: Whether to proxy video content
- `SOCKS5`: Optional SOCKS5 proxy configuration
- `WORKERS`: Number of backend worker processes

### Example Usage

```bash
PORT=3000 BACKEND_PORT=8005 API_URL=http://192.168.1.100:3000 docker-compose up
```

### WebSocket Connections

The application uses WebSocket for real-time updates. The connection flow is:
1. Frontend connects to `ws://{API_URL}/_event` (API_URL is your frontend interface, e.g. http://192.168.4.5:3000)
2. Caddy proxies the WebSocket connection from frontend port (3000) to backend port (8005)
3. Backend handles the WebSocket connection on port 8005

Note: The API_URL should point to your frontend interface (port 3000) where clients connect. Caddy handles proxying these connections to the backend service (port 8005). Reflex automatically converts http:// to ws:// for WebSocket connections.

If you're having WebSocket connection issues:
1. Check that both ports (3000 and 8005) are exposed
2. Verify Caddy is properly proxying WebSocket connections
3. Check browser console for connection errors
4. Ensure `API_URL` is correctly set to your server's address 

# Check environment variables in the container
To see what environment variables are set in the running container:

```bash
docker exec freesky-step-daddy-live-hd-1 env | findstr "PORT API_URL BACKEND_URI DADDYLIVE_URI PROXY_CONTENT SOCKS5 WORKERS BACKEND_PORT WEBSOCKET_URL REFLEX_ENV REFLEX_FRONTEND_ONLY REFLEX_SKIP_COMPILE REDIS_URL PYTHONUNBUFFERED"
```

Example output:
```
API_URL=http://localhost:8005
BACKEND_URI=http://localhost:8005
DADDYLIVE_URI=https://thedaddy.click
SOCKS5=
PROXY_CONTENT=TRUE
PORT=3000
WORKERS=4
BACKEND_PORT=8005
WEBSOCKET_URL=ws://localhost:8005
REFLEX_ENV=prod
REFLEX_FRONTEND_ONLY=true
REFLEX_SKIP_COMPILE=1
REDIS_URL=redis://localhost
PYTHONUNBUFFERED=1
``` 