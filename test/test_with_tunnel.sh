#!/bin/bash
# Auto-create SSH tunnel and run API test

set -e

POD_HOST="82.221.170.234"
POD_PORT="21286"
LOCAL_PORT="8188"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "LTX-2 ComfyUI API Test (Auto SSH Tunnel)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up SSH tunnel..."
    if [ ! -z "$SSH_PID" ]; then
        kill $SSH_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Kill existing tunnels
pkill -f "ssh.*$LOCAL_PORT:localhost:$LOCAL_PORT" 2>/dev/null || true
sleep 1

# Create SSH tunnel
echo "Creating SSH tunnel..."
ssh -f -N -L $LOCAL_PORT:localhost:$LOCAL_PORT \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ConnectTimeout=20 \
    root@$POD_HOST -p $POD_PORT

# Get tunnel PID
SSH_PID=$(pgrep -f "ssh.*$LOCAL_PORT:localhost:$LOCAL_PORT" | head -1)
echo "✅ SSH tunnel created (PID: $SSH_PID)"

# Wait for tunnel to be ready
echo "Waiting for tunnel..."
sleep 3

# Test connection
echo "Testing connection..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:$LOCAL_PORT --connect-timeout 5 | grep -q "200\|302"; then
    echo "✅ Connection successful"
else
    echo "❌ Connection failed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running API Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run simple test
python3 simple_test.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Test completed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
