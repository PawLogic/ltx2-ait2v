#!/usr/bin/env python3
"""
LTX-2 视频生成测试脚本
通过 ComfyUI API 生成音频驱动的视频
"""
import json
import time
import random
from urllib import request
import os

BASE_URL = "http://localhost:8188"

def upload_file(filepath):
    """上传文件到 ComfyUI"""
    filename = os.path.basename(filepath)
    print(f"Uploading {filename}...")

    with open(filepath, 'rb') as f:
        data = f.read()

    boundary = 'Boundary' + ''.join(random.choices('0123456789', k=16))
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    ).encode() + data + f'\r\n--{boundary}--\r\n'.encode()

    req = request.Request(
        f"{BASE_URL}/upload/image",
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )

    with request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        print(f"✅ Uploaded: {result.get('name')}")
        return result.get('name')

def main():
    # 上传文件
    print("=== Step 1: Uploading Files ===")
    image_name = upload_file('/workspace/ltx_test/test_input.jpg')
    audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')

    # 创建工作流
    print("\n=== Step 2: Creating Workflow ===")
    workflow = {
        "1": {
            "class_type": "LTXVAudioVAELoader",
            "inputs": {}
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
                "text": "A beautiful woman speaking naturally with clear facial expressions",
                "clip": ["4", 0]
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["4", 0]
            }
        },
        "7": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "ltx-2-19b-dev-fp8.safetensors"
            }
        },
        "8": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "image": ["3", 0],
                "audio_latent": ["2", 0],
                "frame_rate": 24,
                "frames": 121
            }
        },
        "9": {
            "class_type": "KSampler",
            "inputs": {
                "seed": random.randint(0, 2**31),
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
        "10": {
            "class_type": "LTXVVideoVAELoader",
            "inputs": {}
        },
        "11": {
            "class_type": "LTXVVideoVAEDecode",
            "inputs": {
                "samples": ["9", 0],
                "vae": ["10", 0]
            }
        },
        "12": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "ltx2_test",
                "format": "video/h264-mp4",
                "images": ["11", 0]
            }
        }
    }

    # 提交任务
    print("\n=== Step 3: Submitting Workflow ===")
    payload = {
        "prompt": workflow,
        "client_id": f"test_{int(time.time())}"
    }

    req = request.Request(
        f"{BASE_URL}/prompt",
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            prompt_id = result.get('prompt_id')
            print(f"✅ Queued! Prompt ID: {prompt_id}")
            print(f"\n=== Generation Started! ===")
            print(f"Output directory: /workspace/ComfyUI/output/")
            print(f"\nMonitor progress:")
            print(f"  curl -s localhost:8188/queue | python3 -m json.tool")
            print(f"\nCheck outputs:")
            print(f"  ls -lht /workspace/ComfyUI/output/ | head -10")
            return prompt_id
    except Exception as e:
        print(f"❌ Error submitting workflow: {e}")
        # 打印详细错误信息
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
