ARG PORT API_URL BACKEND_HOST_URI DADDYLIVE_URI PROXY_CONTENT SOCKS5

# Only set for local/direct access. When TLS is used, the API_URL is assumed to be the same as the frontend.
ARG API_URL

# It uses a reverse proxy to serve the frontend statically and proxy to backend
# from a single exposed port, expecting TLS termination to be handled at the
# edge by the given platform.
FROM python:3.13 AS builder

# Install system dependencies including Node.js and npm
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Verify Node.js and npm installation
RUN node --version && npm --version

RUN mkdir -p /app/.web
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install python app requirements and reflex in the container
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install reflex helper utilities like bun/node
COPY rxconfig.py ./
RUN reflex init

# Copy local context to `/app` inside container (see .dockerignore)
COPY . .

# Make startup script executable
RUN chmod +x /app/start.sh

ARG PORT API_URL BACKEND_HOST_URI DADDYLIVE_URI PROXY_CONTENT SOCKS5 BACKEND_PORT

# Set environment variables for the build
ENV PORT=${PORT:-3232} \
    BACKEND_PORT=${BACKEND_PORT:-8005} \
    REFLEX_API_URL=http://192.168.4.5:${BACKEND_PORT:-8005} \
    API_URL=${API_URL:-http://192.168.4.5:${PORT:-3232}} \
    BACKEND_HOST_URI=${BACKEND_HOST_URI:-""} \
    DADDYLIVE_URI=${DADDYLIVE_URI:-"https://thedaddy.click"} \
    PROXY_CONTENT=${PROXY_CONTENT:-TRUE} \
    SOCKS5=${SOCKS5:-""}

# Download other npm dependencies and compile frontend
RUN mkdir -p /srv && \
    echo "Building frontend with REFLEX_API_URL=$REFLEX_API_URL" && \
    echo "Current directory: $(pwd)" && \
    echo "Node.js version: $(node --version)" && \
    echo "npm version: $(npm --version)" && \
    echo "Reflex version: $(reflex --version)" && \
    (reflex export --loglevel debug --frontend-only --no-zip && \
     echo "Reflex export completed successfully" && \
     ls -la .web/build/client/ && \
     mv .web/build/client/* /srv/ && \
     rm -rf .web && \
     echo "Frontend build successful - contents of /srv:" && \
     ls -la /srv/) || \
    (echo "Reflex export failed, creating minimal frontend" && \
     mkdir -p /srv && \
     echo "<html><body><h1>StepDaddyLiveHD</h1><p>Frontend build failed, but backend is running.</p><p>Check the Docker build logs for more information.</p></body></html>" > /srv/index.html && \
     echo "Minimal frontend created")

# Final image with only necessary files
FROM python:3.13-slim

# Install Caddy, redis server, and Node.js/npm inside final image
RUN apt-get update -y && apt-get install -y \
    caddy \
    redis-server \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm are available in final image
RUN node --version && npm --version

ARG PORT API_URL BACKEND_HOST_URI DADDYLIVE_URI PROXY_CONTENT SOCKS5 BACKEND_PORT
ENV PATH="/app/.venv/bin:$PATH" \
    PORT=${PORT:-3232} \
    BACKEND_PORT=${BACKEND_PORT:-8005} \
    REFLEX_API_URL=http://192.168.4.5:${BACKEND_PORT:-8005} \
    API_URL=${API_URL:-http://192.168.4.5:${PORT:-3232}} \
    BACKEND_HOST_URI=${BACKEND_HOST_URI:-""} \
    DADDYLIVE_URI=${DADDYLIVE_URI:-"https://thedaddy.click"} \
    REDIS_URL=redis://localhost \
    PYTHONUNBUFFERED=1 \
    PROXY_CONTENT=${PROXY_CONTENT:-TRUE} \
    SOCKS5=${SOCKS5:-""} \
    WORKERS=${WORKERS:-4}

WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /srv /srv

# Needed until Reflex properly passes SIGTERM on backend.
STOPSIGNAL SIGKILL

EXPOSE $PORT

# Starting the backend with multiple workers
CMD ["/app/start.sh"]