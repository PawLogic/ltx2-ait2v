#!/usr/bin/env python3
"""
LTX-2 ComfyUI API Test Script
Tests image + audio to video generation via ComfyUI API
"""

import json
import os
import random
import sys
import time
from pathlib import Path
from urllib import request, parse
import base64

# ComfyUI API settings
COMFYUI_HOST = "localhost"
COMFYUI_PORT = "8188"
BASE_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

def test_connection():
    """Test basic connection to ComfyUI"""
    print("Testing connection to ComfyUI...")
    try:
        req = request.Request(f"{BASE_URL}/system_stats")
        with request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            print(f"✅ Connected to ComfyUI")
            print(f"   System: {data.get('system', {})}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def get_object_info():
    """Get available nodes"""
    print("\nFetching object info...")
    try:
        req = request.Request(f"{BASE_URL}/object_info")
        with request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            ltx_nodes = [k for k in data.keys() if 'LTX' in k.upper()]
            print(f"✅ Found {len(ltx_nodes)} LTX nodes")
            print(f"   Nodes: {ltx_nodes[:5]}")
            return data
    except Exception as e:
        print(f"❌ Failed to get object info: {e}")
        return None

def upload_file(filepath, subfolder="", overwrite=False):
    """Upload file to ComfyUI"""
    filename = Path(filepath).name
    print(f"\nUploading {filename}...")

    try:
        with open(filepath, 'rb') as f:
            file_data = f.read()

        # Prepare multipart form data
        boundary = '----WebKitFormBoundary' + ''.join(random.choices('0123456789abcdef', k=16))
        body = []

        # Add file data
        body.append(f'--{boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"'.encode())
        body.append(b'Content-Type: application/octet-stream')
        body.append(b'')
        body.append(file_data)

        # Add subfolder if provided
        if subfolder:
            body.append(f'--{boundary}'.encode())
            body.append(b'Content-Disposition: form-data; name="subfolder"')
            body.append(b'')
            body.append(subfolder.encode())

        # Add overwrite flag
        body.append(f'--{boundary}'.encode())
        body.append(b'Content-Disposition: form-data; name="overwrite"')
        body.append(b'')
        body.append(str(overwrite).lower().encode())

        body.append(f'--{boundary}--'.encode())
        body.append(b'')

        body_bytes = b'\r\n'.join(body)

        req = request.Request(
            f"{BASE_URL}/upload/image",
            data=body_bytes,
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Content-Length': str(len(body_bytes))
            }
        )

        with request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
            print(f"✅ Uploaded: {result.get('name', filename)}")
            return result
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None

def queue_prompt(workflow):
    """Submit workflow to queue"""
    print("\nSubmitting workflow to queue...")

    prompt_id = f"test_{int(time.time())}"

    payload = {
        "prompt": workflow,
        "client_id": prompt_id
    }

    try:
        req = request.Request(
            f"{BASE_URL}/prompt",
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'}
        )

        with request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
            print(f"✅ Queued with ID: {result.get('prompt_id', 'unknown')}")
            return result
    except Exception as e:
        print(f"❌ Queue failed: {e}")
        return None

def get_history(prompt_id):
    """Get execution history for a prompt"""
    try:
        req = request.Request(f"{BASE_URL}/history/{prompt_id}")
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"❌ Failed to get history: {e}")
        return None

def check_queue():
    """Check current queue status"""
    try:
        req = request.Request(f"{BASE_URL}/queue")
        with request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            running = len(data.get('queue_running', []))
            pending = len(data.get('queue_pending', []))
            print(f"Queue status: {running} running, {pending} pending")
            return data
    except Exception as e:
        print(f"❌ Failed to check queue: {e}")
        return None

def create_simple_workflow(image_name, audio_name):
    """Create a simple LTX-2 workflow"""
    workflow = {
        "1": {
            "class_type": "LTXVAudioVAELoader",
            "inputs": {
                "model_name": "MelBandRoformer_FP16.ckpt"
            }
        },
        "2": {
            "class_type": "LTXVAudioVAEEncode",
            "inputs": {
                "audio": audio_name,
                "vae": ["1", 0]
            }
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_name
            }
        },
        "4": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {}
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "A person speaking with natural lip movements",
                "clip": ["4", 0]
            }
        }
    }
    return workflow

def main():
    print("=" * 60)
    print("LTX-2 ComfyUI API Test")
    print("=" * 60)

    # Step 1: Test connection
    if not test_connection():
        print("\n❌ Cannot connect to ComfyUI. Make sure SSH tunnel is running:")
        print("   ssh -L 8188:localhost:8188 root@82.221.170.234 -p 21286")
        sys.exit(1)

    # Step 2: Get available nodes
    obj_info = get_object_info()
    if not obj_info:
        sys.exit(1)

    # Step 3: Check queue
    print("\nChecking queue status...")
    check_queue()

    # Step 4: Upload test files
    test_dir = Path(__file__).parent
    image_path = test_dir / "test_input.jpg"
    audio_path = test_dir / "test_audio.mp3"

    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)

    if not audio_path.exists():
        print(f"❌ Audio not found: {audio_path}")
        sys.exit(1)

    # Upload files
    image_result = upload_file(str(image_path))
    if not image_result:
        sys.exit(1)

    audio_result = upload_file(str(audio_path))
    if not audio_result:
        sys.exit(1)

    # Step 5: Create and submit workflow
    print("\nCreating workflow...")
    workflow = create_simple_workflow(
        image_result.get('name', 'test_input.jpg'),
        audio_result.get('name', 'test_audio.mp3')
    )
    print(json.dumps(workflow, indent=2))

    # Step 6: Queue prompt
    result = queue_prompt(workflow)
    if result:
        prompt_id = result.get('prompt_id')
        print(f"\n✅ Workflow queued successfully!")
        print(f"   Prompt ID: {prompt_id}")
        print(f"   Monitor at: {BASE_URL}")

        # Wait a bit and check history
        time.sleep(2)
        history = get_history(prompt_id)
        if history:
            print(f"\n📊 History: {json.dumps(history, indent=2)[:500]}...")

    print("\n" + "=" * 60)
    print("✅ API test completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
