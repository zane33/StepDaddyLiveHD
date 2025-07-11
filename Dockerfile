# Build stage
FROM python:3.13 AS builder

# Install system dependencies including Node.js and npm
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    dos2unix \
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

# Copy local context to `/app` inside container (see .dockerignore)
COPY . .

# Convert start.sh to Unix line endings and make it executable
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

ARG PORT BACKEND_PORT API_URL DADDYLIVE_URI PROXY_CONTENT SOCKS5

# Set environment variables for the build
ENV PORT=${PORT:-3232} \
    BACKEND_PORT=${BACKEND_PORT:-8005} \
    BACKEND_URI=${BACKEND_URI:-http://localhost:${BACKEND_PORT:-8005}} \
    API_URL=${API_URL:-http://localhost:${PORT:-3232}} \
    DADDYLIVE_URI=${DADDYLIVE_URI:-"https://thedaddy.click"} \
    PROXY_CONTENT=${PROXY_CONTENT:-TRUE} \
    SOCKS5=${SOCKS5:-""} \
    REFLEX_ENV=prod \
    REFLEX_FRONTEND_ONLY=true

# Initialize Reflex and build frontend
RUN echo "Building frontend with API_URL=$API_URL" && \
    echo "Current directory: $(pwd)" && \
    echo "Node.js version: $(node --version)" && \
    echo "npm version: $(npm --version)" && \
    echo "Reflex version: $(reflex --version)" && \
    mkdir -p /srv && \
    (cd /app && \
     reflex init && \
     cd .web && \
     npm install --legacy-peer-deps && \
     cd .. && \
     reflex export --frontend-only --no-zip && \
     mv .web/build/client/* /srv/ && \
     rm -rf .web && \
     echo "Frontend build successful - contents of /srv:" && \
     ls -la /srv/) || \
    (echo "Frontend build failed, creating minimal frontend" && \
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
    dos2unix \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm are available in final image
RUN node --version && npm --version

ARG PORT BACKEND_PORT API_URL DADDYLIVE_URI PROXY_CONTENT SOCKS5
ENV PATH="/app/.venv/bin:$PATH" \
    PORT=${PORT:-3232} \
    BACKEND_PORT=${BACKEND_PORT:-8005} \
    BACKEND_URI=${BACKEND_URI:-http://localhost:${BACKEND_PORT:-8005}} \
    API_URL=${API_URL:-http://localhost:${PORT:-3232}} \
    DADDYLIVE_URI=${DADDYLIVE_URI:-"https://thedaddy.click"} \
    REDIS_URL=redis://localhost \
    PYTHONUNBUFFERED=1 \
    PROXY_CONTENT=${PROXY_CONTENT:-TRUE} \
    SOCKS5=${SOCKS5:-""} \
    WORKERS=${WORKERS:-6} \
    REFLEX_ENV=prod \
    REFLEX_FRONTEND_ONLY=true \
    REFLEX_SKIP_COMPILE=1

WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /srv /srv

# Convert start.sh to Unix line endings and make it executable in the final image
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# Needed until Reflex properly passes SIGTERM on backend.
STOPSIGNAL SIGKILL

EXPOSE $PORT $BACKEND_PORT

# Starting the backend with multiple workers
CMD ["/app/start.sh"]