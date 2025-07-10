# Troubleshooting Guide

## Common Issues and Solutions

### 1. Connection Refused Error (Port 8000)

**Error**: `dial tcp 127.0.0.1:8000: connect: connection refused`

**Cause**: The backend is not running on port 8000 as expected by Caddy.

**Solutions**:
- Check if the container is running: `docker ps`
- Check container logs: `docker logs <container_name>`
- Verify the backend started properly by looking for "Backend initialized" in logs
- Test the backend directly: `curl http://localhost:8000/ping`

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
- Increase `WORKERS` environment variable (default: 4, recommended: 4-8)
- Monitor system resources (CPU, memory)
- Check cache hit rates using `/health` endpoint
- Use the performance monitoring script: `python monitor_performance.py http://localhost:${PORT:-3232}`

## Performance Optimizations

### Environment Variables for Performance

- `WORKERS`: Number of worker processes (default: 4, recommended: 4-8 for most deployments)
- `PROXY_CONTENT`: Whether to proxy content (default: TRUE)
- `SOCKS5`: SOCKS5 proxy configuration (optional)

### Caching

The application now includes several caching mechanisms:
- **Stream Cache**: Caches M3U8 playlists for 5 minutes
- **Logo Cache**: Caches channel logos for 24 hours
- **Channel Cache**: Caches channel list with LRU eviction

### Connection Pooling

- HTTP client uses connection pooling with up to 100 connections
- Keep-alive connections for better performance
- Automatic retry logic for failed requests

### Rate Limiting

- Caddy includes rate limiting (100 requests per 10 seconds)
- Backend includes semaphore limiting (10 concurrent stream requests)

## Debugging Steps

### 1. Check Container Status
```bash
docker ps -a
docker logs <container_name>
```

### 2. Test Backend Directly
```bash
# If running locally
python test_backend.py

# If running in container
docker exec <container_name> python test_backend.py
```

### 3. Check Service Health
```bash
# Test Caddy
curl http://localhost:${PORT:-3232}/ping

# Test backend directly
curl http://localhost:8000/ping

# Check detailed health status
curl http://localhost:${PORT:-3232}/health
```

### 4. Check Environment Variables
```bash
docker exec <container_name> env | grep -E "(PORT|API_URL|BACKEND_HOST_URI|DADDYLIVE_URI|PROXY_CONTENT|SOCKS5|WORKERS)"
```

### 5. Performance Monitoring
```bash
# Run performance tests
python monitor_performance.py http://localhost:${PORT:-3232}

# Check system resources
docker stats <container_name>
```

## Environment Variables

The application supports the following environment variables:

- `PORT`: The port Caddy listens on (default: 3232)
- `API_URL`: The API URL for the frontend (optional)
- `BACKEND_HOST_URI`: The backend host URI for custom backend configuration (optional)
- `DADDYLIVE_URI`: The daddylive endpoint URI (default: https://thedaddy.click)
- `PROXY_CONTENT`: Whether to proxy content (default: TRUE)
- `SOCKS5`: SOCKS5 proxy configuration (optional)
- `WORKERS`: Number of worker processes for better performance (default: 4)

### BACKEND_HOST_URI Usage

The `BACKEND_HOST_URI` environment variable allows you to configure a custom backend host URI. This is useful when:

- The backend needs to be accessible from a different host than the frontend
- You're running the backend on a different port or domain
- You need to configure the backend for external access

Example usage:
```bash
# Set in .env file
BACKEND_HOST_URI=http://backend.example.com:8000

# Or when running docker-compose
BACKEND_HOST_URI=http://backend.example.com:8000 docker-compose up
```

### WORKERS Configuration

The `WORKERS` environment variable controls the number of worker processes for better multi-connection handling:

```bash
# For development (single worker)
WORKERS=1

# For production (recommended)
WORKERS=4

# For high-traffic deployments
WORKERS=8
```

## Log Files

The application logs important events including:
- Backend initialization
- Channel loading attempts
- Network errors
- Service startup status
- Cache hit/miss statistics
- Performance metrics

Check logs for specific error messages and timestamps to identify issues.

## Performance Tuning

### For High-Traffic Deployments

1. **Increase Workers**: Set `WORKERS=8` or higher
2. **Monitor Resources**: Use `docker stats` to monitor CPU and memory usage
3. **Cache Optimization**: Monitor cache hit rates via `/health` endpoint
4. **Network Optimization**: Consider using a CDN for static content
5. **Load Balancing**: Use multiple container instances behind a load balancer

### For Low-Resource Environments

1. **Reduce Workers**: Set `WORKERS=2` or `WORKERS=1`
2. **Disable Content Proxy**: Set `PROXY_CONTENT=FALSE`
3. **Monitor Memory**: Watch for memory leaks or high usage
4. **Optimize Caching**: Reduce cache TTL if memory is limited 