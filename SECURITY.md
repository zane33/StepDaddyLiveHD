# Security Configuration Guide

This document outlines the security configurations and best practices implemented in freesky.

## Content Security Policy (CSP)

### Overview
Content Security Policy is implemented at multiple layers to ensure secure content delivery while maintaining functionality:

1. **Frontend CSP (Reflex Configuration)**
   ```python
   # Configured in rxconfig.py
   "Content-Security-Policy": {
       "default-src": "'self'",
       "script-src": "'self' 'unsafe-eval' 'unsafe-inline'",  # Required for Reflex and video player
       "style-src": "'self' 'unsafe-inline'",  # Required for styled-components
       "img-src": "'self' data: https:",  # Allow images from HTTPS sources
       "media-src": "'self' blob: *",  # Required for video streaming
       "connect-src": "'self' ws: wss: *",  # Required for WebSocket and API
       "worker-src": "'self' blob:",  # Required for video processing
       "frame-src": "'self' *",  # Required for video iframes
       "font-src": "'self' data:"  # Allow fonts
   }
   ```

2. **Additional Security Headers**
   - `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
   - `X-Frame-Options: DENY` - Prevents clickjacking
   - `X-XSS-Protection: 1; mode=block` - Enables browser XSS protection
   - `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer information
   - `Permissions-Policy: geolocation=(), microphone=(), camera=()` - Restricts browser features

### CSP Exceptions
Certain CSP directives are intentionally relaxed to support required functionality:

1. **'unsafe-eval' in script-src**
   - Required by: Reflex framework, Video player components
   - Impact: Allows dynamic code evaluation
   - Mitigation: Limited to necessary framework operations

2. **'unsafe-inline' in style-src**
   - Required by: Styled-components, Dynamic styling
   - Impact: Allows inline styles
   - Mitigation: Limited to CSS only

3. **Wildcard (*) in media-src and frame-src**
   - Required by: Video streaming functionality
   - Impact: Allows loading media from external sources
   - Mitigation: Content is proxied through backend when PROXY_CONTENT=TRUE

## Reverse Proxy Security

### Frontend to Backend Communication
```plaintext
[Client] <-> [Caddy (Frontend)] <-> [Backend API]
```

1. **Caddy Server Configuration**
   - Handles SSL/TLS termination
   - Implements security headers
   - Manages WebSocket upgrades
   - Proxies API requests to backend

2. **CORS Configuration**
   ```python
   # Configured in backend.py
   CORSMiddleware(
       allow_origins=[api_url, ws_url, "*"],  # Controlled by environment
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"]
   )
   ```

### Content Proxying
Two modes of operation controlled by PROXY_CONTENT environment variable:

1. **PROXY_CONTENT=TRUE (Default, Recommended)**
   - All video content proxied through backend
   - Original URLs hidden from clients
   - Better CORS handling
   - Enhanced privacy and control

2. **PROXY_CONTENT=FALSE**
   - Direct client-to-source connections
   - Lower server load
   - Less privacy
   - Potential CORS issues

## Network Security

### Docker Network Configuration
```yaml
# Configured in docker-compose.yml
networks:
  step-daddy-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_ip_masquerade: "true"
      com.docker.network.bridge.enable_icc: "true"
```

### DNS Configuration
- Primary: Google DNS (8.8.8.8)
- Backup: Cloudflare DNS (1.1.1.1)

### Proxy Support
- Optional SOCKS5 proxy support
- HTTP/HTTPS proxy support via environment variables
- Configurable NO_PROXY for local development

## Rate Limiting and DDoS Protection

1. **Stream Request Limiting**
   ```python
   # Configured in free_sky.py
   self._stream_semaphore = asyncio.Semaphore(10)  # Limit concurrent streams
   ```

2. **Connection Timeouts**
   ```python
   # Configured in free_sky.py
   session_config = {
       "timeout": 30,  # 30 second timeout
       "max_redirects": 5  # Limit redirect chains
   }
   ```

## Development vs Production

### Development Mode
- More permissive CSP
- Local network access
- Debug logging enabled
- Single worker process

### Production Mode
- Strict CSP
- Rate limiting enabled
- Multiple worker processes
- Proxy content enabled by default

## Security Best Practices

1. **Environment Variables**
   - Use `.env` file for local development
   - Use secure secrets management in production
   - Never commit sensitive values to version control

2. **API Keys and Secrets**
   - Store in environment variables
   - Rotate regularly
   - Use separate keys for development/production

3. **Error Handling**
   - Sanitize error messages
   - Log securely
   - Don't expose internal details to clients

4. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Regular security audits

## Troubleshooting

### Common CSP Issues
1. **Video Player Not Loading**
   - Check browser console for CSP violations
   - Verify media-src and frame-src directives
   - Ensure WebSocket connections allowed

2. **Style Issues**
   - Verify style-src includes 'unsafe-inline'
   - Check for blocked font or image resources
   - Validate data: URIs if used

3. **API Connection Issues**
   - Verify connect-src configuration
   - Check WebSocket upgrade headers
   - Validate CORS settings

## Future Security Enhancements

1. **Planned Improvements**
   - Implement request signing
   - Add API rate limiting
   - Enhanced logging and monitoring
   - Security headers presets

2. **Under Consideration**
   - OAuth integration
   - IP geolocation filtering
   - Enhanced DDoS protection
   - Certificate pinning 