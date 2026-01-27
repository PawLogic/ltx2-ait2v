#!/usr/bin/env python3
"""
LTX-2 最简测试脚本 - 不包含 VAE 解码和视频保存
用于快速验证工作流是否能正确排队
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
    print(f"📤 Uploading {filename}...")

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
        print(f"   ✅ {result.get('name')}")
        return result.get('name')

def check_comfyui():
    """检查 ComfyUI 状态"""
    print("🔍 Checking ComfyUI status...")
    try:
        req = request.Request(f"{BASE_URL}/system_stats")
        with request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"   ✅ ComfyUI {data['system']['comfyui_version']}")
            print(f"   ✅ PyTorch {data['system']['pytorch_version']}")
            return True
    except Exception as e:
        print(f"   ❌ ComfyUI not responding: {e}")
        return False

def main():
    print("=" * 60)
    print("LTX-2 Simple Test Script")
    print("=" * 60)

    # 检查 ComfyUI
    if not check_comfyui():
        return

    print("\n📁 Step 1: Uploading files...")
    try:
        image_name = upload_file('/workspace/ltx_test/test_input.jpg')
        audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    # 最简工作流 - 只到 latent 阶段
    print("\n🔧 Step 2: Creating minimal workflow...")
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
                "text": "woman speaking",
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
        }
    }

    print("\n🚀 Step 3: Submitting to ComfyUI...")
    payload = {
        "prompt": workflow,
        "client_id": f"simple_test_{int(time.time())}"
    }

    req = request.Request(
        f"{BASE_URL}/prompt",
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            response_data = resp.read()
            result = json.loads(response_data)

            if 'error' in result:
                print(f"❌ Workflow error: {result['error']}")
                if 'node_errors' in result:
                    print(f"   Node errors: {json.dumps(result['node_errors'], indent=2)}")
                return

            prompt_id = result.get('prompt_id')
            print(f"✅ Success! Prompt ID: {prompt_id}")
            print("\n" + "=" * 60)
            print("Next steps:")
            print("  1. Monitor queue: curl -s localhost:8188/queue | python3 -m json.tool")
            print("  2. Check history: curl -s localhost:8188/history | python3 -m json.tool")
            print("=" * 60)
            return prompt_id

    except request.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        error_body = e.read().decode('utf-8')
        print(f"   Response: {error_body}")
        try:
            error_data = json.loads(error_body)
            if 'error' in error_data:
                print(f"   Error detail: {error_data['error']}")
            if 'node_errors' in error_data:
                print(f"   Node errors: {json.dumps(error_data['node_errors'], indent=2)}")
        except:
            pass
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
