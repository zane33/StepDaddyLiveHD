#!/bin/bash

echo "Starting StepDaddyLiveHD services..."

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
echo "Starting Reflex backend with $WORKERS workers..."

# Start the backend with multiple workers using uvicorn directly
cd /app && exec uvicorn StepDaddyLiveHD.StepDaddyLiveHD:app --host 0.0.0.0 --port 8000 --workers $WORKERS 