#!/usr/bin/env python3
"""
Run LTX-2 video generation directly on Pod
"""

import json
import time
import random
from urllib import request

BASE_URL = "http://localhost:8188"

# Upload image
print("Uploading test_input.jpg...")
with open('/tmp/test_input.jpg', 'rb') as f:
    image_data = f.read()

boundary = 'WebKitFormBoundary' + ''.join(random.choices('0123456789abcdef', k=16))
body = []
body.append(f'--{boundary}'.encode())
body.append(b'Content-Disposition: form-data; name="image"; filename="test_input.jpg"')
body.append(b'Content-Type: application/octet-stream')
body.append(b'')
body.append(image_data)
body.append(f'--{boundary}'.encode())
body.append(b'Content-Disposition: form-data; name="overwrite"')
body.append(b'')
body.append(b'true')
body.append(f'--{boundary}--'.encode())
body.append(b'')

req = request.Request(
    f"{BASE_URL}/upload/image",
    data=b'\r\n'.join(body),
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
with request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(f"Image uploaded: {result.get('name')}")
    image_name = result.get('name')

# Upload audio
print("Uploading test_audio.mp3...")
with open('/tmp/test_audio.mp3', 'rb') as f:
    audio_data = f.read()

boundary = 'WebKitFormBoundary' + ''.join(random.choices('0123456789abcdef', k=16))
body = []
body.append(f'--{boundary}'.encode())
body.append(b'Content-Disposition: form-data; name="image"; filename="test_audio.mp3"')
body.append(b'Content-Type: application/octet-stream')
body.append(b'')
body.append(audio_data)
body.append(f'--{boundary}'.encode())
body.append(b'Content-Disposition: form-data; name="overwrite"')
body.append(b'')
body.append(b'true')
body.append(f'--{boundary}--'.encode())
body.append(b'')

req = request.Request(
    f"{BASE_URL}/upload/image",
    data=b'\r\n'.join(body),
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
with request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(f"Audio uploaded: {result.get('name')}")
    audio_name = result.get('name')

# Create workflow
print("Creating workflow...")
workflow = {
    "1": {"class_type": "LTXVAudioVAELoader", "inputs": {}},
    "2": {"class_type": "LTXVAudioVAEEncode", "inputs": {"audio": audio_name, "vae": ["1", 0]}},
    "3": {"class_type": "LoadImage", "inputs": {"image": image_name}},
    "4": {"class_type": "LTXAVTextEncoderLoader", "inputs": {}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "A beautiful woman speaking naturally with perfect lip sync", "clip": ["4", 0]}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 0]}},
    "7": {"class_type": "UNETLoader", "inputs": {"unet_name": "ltx-2-19b-dev-fp8.safetensors"}},
    "8": {"class_type": "LTXVImgToVideo", "inputs": {"image": ["3", 0], "audio_latent": ["2", 0], "frame_rate": 24, "frames": 121}},
    "9": {"class_type": "KSampler", "inputs": {"seed": random.randint(0, 2**32-1), "steps": 20, "cfg": 3.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["7", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["8", 0]}},
    "10": {"class_type": "VAELoader", "inputs": {"vae_name": "ltx-2-vae.safetensors"}},
    "11": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["10", 0]}},
    "12": {"class_type": "VHS_VideoCombine", "inputs": {"frame_rate": 24, "loop_count": 0, "filename_prefix": "ltx2_test", "format": "video/h264-mp4", "images": ["11", 0]}}
}

# Submit workflow
print("Submitting workflow...")
payload = {"prompt": workflow, "client_id": f"test_{int(time.time())}"}
req = request.Request(
    f"{BASE_URL}/prompt",
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'}
)
with request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    prompt_id = result.get('prompt_id')
    print(f"✅ Queued: {prompt_id}")
    print(f"Monitor at: {BASE_URL}")

print("\nVideo generation started!")
print("Check output at: /workspace/ComfyUI/output/")
