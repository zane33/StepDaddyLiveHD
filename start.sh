#!/bin/bash

echo "Starting StepDaddyLiveHD services..."

# Check internet connectivity
echo "Checking internet connectivity..."
if ! curl -s --connect-timeout 5 https://8.8.8.8 >/dev/null; then
    echo "Warning: Cannot reach internet (IP connectivity test failed)"
fi

if ! curl -s --connect-timeout 5 https://www.google.com >/dev/null; then
    echo "Warning: Cannot resolve DNS (DNS resolution test failed)"
fi

# Test connection to DADDYLIVE_URI
echo "Testing connection to content provider..."
if ! curl -s --connect-timeout 10 "${DADDYLIVE_URI:-https://thedaddy.click}" >/dev/null; then
    echo "Warning: Cannot connect to content provider at ${DADDYLIVE_URI:-https://thedaddy.click}"
fi

# Set environment variables to prevent frontend compilation at runtime
export REFLEX_ENV=prod
export REFLEX_FRONTEND_ONLY=true
export REFLEX_SKIP_COMPILE=1

# Start Redis in the background
echo "Starting Redis..."
redis-server --daemonize yes

# Wait for Redis to start
echo "Waiting for Redis..."
until redis-cli ping &>/dev/null; do
    sleep 1
done
echo "Redis started successfully"

# Get number of workers from environment or use default
WORKERS=${WORKERS:-6}
# Get backend port from environment or use default
BACKEND_PORT=${BACKEND_PORT:-8005}
echo "Starting Reflex backend with $WORKERS workers on port $BACKEND_PORT..."

# Start the backend with multiple workers using the FastAPI app
cd /app && uvicorn StepDaddyLiveHD.backend_app:fastapi_app --host 0.0.0.0 --port $BACKEND_PORT --workers $WORKERS &

# Wait for backend to be ready
echo "Waiting for backend..."
until curl -s http://localhost:$BACKEND_PORT/health &>/dev/null; do
    sleep 1
done
echo "Backend started successfully"

# Start Caddy in the foreground with explicit configuration
echo "Starting Caddy..."
exec caddy run --config /app/Caddyfile --adapter caddyfile 