#!/bin/bash
# Test ComfyUI API via Jupyter terminal
JUPYTER_URL="https://kl34b69nag9f1b-8888.proxy.runpod.net"

echo "Testing ComfyUI API via Jupyter..."
echo "Jupyter URL: $JUPYTER_URL"
echo ""
echo "You can manually test in Jupyter terminal:"
echo "1. Open: $JUPYTER_URL"
echo "2. Go to terminal"
echo "3. Run: curl localhost:8188/system_stats | python3 -m json.tool"
echo ""
echo "Or test LTX nodes:"
echo "curl localhost:8188/object_info | python3 -c \"import sys,json; data=json.load(sys.stdin); print([k for k in data.keys() if 'LTX' in k.upper()])\""
