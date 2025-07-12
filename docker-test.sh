#\!/bin/bash
# Test if we can access Docker with proper permissions
sudo usermod -aG docker $USER
sudo service docker start 2>/dev/null || echo "Docker service not managed by systemd"
echo "Testing Docker access..."
timeout 10 docker version 2>&1 || echo "Docker access failed"
