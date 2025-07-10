#!/bin/bash

echo "Starting StepDaddyLiveHD services..."

# Set environment variables to prevent frontend compilation at runtime
export REFLEX_ENV=prod
export REFLEX_FRONTEND_ONLY=true

# Start Redis in the background
echo "Starting Redis..."
redis-server --daemonize yes

# Wait for Redis to start
echo "Waiting for Redis..."
until redis-cli ping &>/dev/null; do
    sleep 1
done
echo "Redis started successfully"

# Start Caddy
echo "Starting Caddy..."
caddy start

# Wait for Caddy to be ready
echo "Waiting for Caddy..."
until curl -s http://localhost:2019/config/ &>/dev/null; do
    sleep 1
done
echo "Caddy started successfully"

# Get number of workers from environment or use default
WORKERS=${WORKERS:-4}
# Get backend port from environment or use default
BACKEND_PORT=${BACKEND_PORT:-8000}
echo "Starting Reflex backend with $WORKERS workers on port $BACKEND_PORT..."

# Start the backend with multiple workers using the Socket.IO app
cd /app && exec uvicorn StepDaddyLiveHD.backend_app:socket_app --host 0.0.0.0 --port $BACKEND_PORT --workers $WORKERS 