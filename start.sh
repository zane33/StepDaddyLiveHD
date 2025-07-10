#!/bin/bash

echo "Starting StepDaddyLiveHD services..."

# Start Caddy in the background
echo "Starting Caddy..."
caddy start --config /etc/caddy/Caddyfile &
CADDY_PID=$!

# Start Redis in the background
echo "Starting Redis..."
redis-server --daemonize yes

# Wait a moment for services to start
sleep 2

# Check if Caddy is running
if kill -0 $CADDY_PID 2>/dev/null; then
    echo "Caddy started successfully (PID: $CADDY_PID)"
else
    echo "Failed to start Caddy"
    exit 1
fi

# Check if Redis is running
if redis-cli ping >/dev/null 2>&1; then
    echo "Redis started successfully"
else
    echo "Failed to start Redis"
    exit 1
fi

# Get number of workers from environment or use default
WORKERS=${WORKERS:-4}
echo "Starting Reflex backend with $WORKERS workers..."

# Start the backend with multiple workers using uvicorn
exec reflex run --env prod --backend-only --backend-port 8000 --workers $WORKERS 