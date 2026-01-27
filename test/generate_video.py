#!/usr/bin/env python3
"""
LTX-2 Audio-to-Video Generation Test
Generates video from image + audio using ComfyUI API
"""

import json
import os
import random
import sys
import time
from pathlib import Path
from urllib import request
import urllib.error

BASE_URL = "http://localhost:8188"

def upload_file(filepath, subfolder="", overwrite=True):
    """Upload file to ComfyUI"""
    filename = Path(filepath).name
    print(f"Uploading {filename}...")

    try:
        with open(filepath, 'rb') as f:
            file_data = f.read()

        boundary = '----WebKitFormBoundary' + ''.join(random.choices('0123456789abcdef', k=16))
        body = []

        body.append(f'--{boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"'.encode())
        body.append(b'Content-Type: application/octet-stream')
        body.append(b'')
        body.append(file_data)

        if subfolder:
            body.append(f'--{boundary}'.encode())
            body.append(b'Content-Disposition: form-data; name="subfolder"')
            body.append(b'')
            body.append(subfolder.encode())

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

def create_ltx2_workflow(image_name, audio_name, prompt="A woman speaking naturally with lip sync"):
    """Create LTX-2 audio-to-video workflow"""

    workflow = {
        # 1. Load Audio VAE
        "1": {
            "class_type": "LTXVAudioVAELoader",
            "inputs": {}
        },

        # 2. Encode Audio
        "2": {
            "class_type": "LTXVAudioVAEEncode",
            "inputs": {
                "audio": audio_name,
                "vae": ["1", 0]
            }
        },

        # 3. Load Image
        "3": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_name
            }
        },

        # 4. Load Text Encoder
        "4": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {}
        },

        # 5. Encode Prompt
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["4", 0]
            }
        },

        # 6. Empty Negative Prompt
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["4", 0]
            }
        },

        # 7. Load UNET Model
        "7": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "ltx-2-19b-dev-fp8.safetensors"
            }
        },

        # 8. Image to Video Latent
        "8": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "image": ["3", 0],
                "audio_latent": ["2", 0],
                "frame_rate": 24,
                "frames": 121  # ~5 seconds at 24fps
            }
        },

        # 9. KSampler
        "9": {
            "class_type": "KSampler",
            "inputs": {
                "seed": random.randint(0, 2**32 - 1),
                "steps": 20,
                "cfg": 3.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["7", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["8", 0]
            }
        },

        # 10. Load VAE
        "10": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ltx-2-vae.safetensors"
            }
        },

        # 11. VAE Decode
        "11": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["9", 0],
                "vae": ["10", 0]
            }
        },

        # 12. Save Video
        "12": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "ltx2_output",
                "format": "video/h264-mp4",
                "images": ["11", 0]
            }
        }
    }

    return workflow

def queue_prompt(workflow):
    """Submit workflow to queue"""
    print("\nSubmitting workflow...")

    client_id = f"test_{int(time.time())}"

    payload = {
        "prompt": workflow,
        "client_id": client_id
    }

    try:
        req = request.Request(
            f"{BASE_URL}/prompt",
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'}
        )

        with request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
            prompt_id = result.get('prompt_id')
            print(f"✅ Queued with prompt_id: {prompt_id}")
            return prompt_id
    except Exception as e:
        print(f"❌ Queue failed: {e}")
        return None

def get_history(prompt_id):
    """Get execution history"""
    try:
        req = request.Request(f"{BASE_URL}/history/{prompt_id}")
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except Exception as e:
        return None

def check_queue():
    """Check queue status"""
    try:
        req = request.Request(f"{BASE_URL}/queue")
        with request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data
    except Exception as e:
        return None

def wait_for_completion(prompt_id, timeout=600):
    """Wait for prompt to complete"""
    print("\nWaiting for generation to complete...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check history
        history = get_history(prompt_id)
        if history and prompt_id in history:
            status = history[prompt_id].get('status', {})

            if status.get('completed', False):
                print("✅ Generation completed!")
                return history[prompt_id]

            if 'error' in status or status.get('status_str') == 'error':
                print(f"❌ Generation failed: {status}")
                return None

        # Check queue
        queue = check_queue()
        if queue:
            running = queue.get('queue_running', [])
            pending = queue.get('queue_pending', [])

            # Check if our prompt is in queue
            in_queue = any(item[1] == prompt_id for item in running + pending)

            if not in_queue and history and prompt_id not in history:
                print("⚠️ Prompt not in queue and not in history")

            print(f"Queue: {len(running)} running, {len(pending)} pending", end='\r')

        time.sleep(2)

    print("\n❌ Timeout waiting for completion")
    return None

def main():
    print("=" * 70)
    print("LTX-2 Audio-to-Video Generation")
    print("=" * 70)

    # Check connection
    try:
        req = request.Request(f"{BASE_URL}/system_stats")
        with request.urlopen(req, timeout=10) as response:
            print("✅ Connected to ComfyUI")
    except Exception as e:
        print(f"❌ Cannot connect to ComfyUI: {e}")
        print("Make sure SSH tunnel is running:")
        print("  ssh -L 8188:localhost:8188 root@82.221.170.234 -p 21286")
        sys.exit(1)

    # Get test files
    test_dir = Path(__file__).parent
    image_path = test_dir / "test_input.jpg"
    audio_path = test_dir / "test_audio.mp3"

    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)

    if not audio_path.exists():
        print(f"❌ Audio not found: {audio_path}")
        sys.exit(1)

    print(f"\nInput files:")
    print(f"  Image: {image_path.name} ({image_path.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"  Audio: {audio_path.name} ({audio_path.stat().st_size / 1024:.2f} KB)")

    # Upload files
    print("\n" + "-" * 70)
    image_result = upload_file(str(image_path))
    if not image_result:
        sys.exit(1)

    audio_result = upload_file(str(audio_path))
    if not audio_result:
        sys.exit(1)

    # Create workflow
    print("\n" + "-" * 70)
    print("Creating workflow...")
    workflow = create_ltx2_workflow(
        image_result.get('name', 'test_input.jpg'),
        audio_result.get('name', 'test_audio.mp3'),
        prompt="A beautiful woman speaking naturally with perfect lip synchronization"
    )
    print(f"✅ Workflow created with {len(workflow)} nodes")

    # Queue prompt
    print("\n" + "-" * 70)
    prompt_id = queue_prompt(workflow)
    if not prompt_id:
        sys.exit(1)

    # Wait for completion
    print("-" * 70)
    result = wait_for_completion(prompt_id, timeout=600)

    if result:
        print("\n" + "=" * 70)
        print("✅ Video generation successful!")
        print("=" * 70)

        # Get output info
        outputs = result.get('outputs', {})
        for node_id, output in outputs.items():
            if 'gifs' in output:
                for gif in output['gifs']:
                    print(f"\n📹 Output video:")
                    print(f"   Filename: {gif.get('filename')}")
                    print(f"   Subfolder: {gif.get('subfolder', 'output')}")
            if 'images' in output:
                print(f"   Generated {len(output['images'])} frames")

        print(f"\n💾 Check ComfyUI output folder on Pod:")
        print(f"   /workspace/ComfyUI/output/")
    else:
        print("\n" + "=" * 70)
        print("❌ Video generation failed")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
