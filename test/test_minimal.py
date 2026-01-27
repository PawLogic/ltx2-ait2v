#!/usr/bin/env python3
"""
LTX-2 最小化测试脚本
使用当前 API 的正确节点和参数
基于诊断结果修正的工作流
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

def create_minimal_workflow(image_name, audio_name, seed=None):
    """
    创建最小化工作流
    使用 UNETLoader 代替 CheckpointLoaderSimple
    修正所有节点参数以匹配当前 API
    """
    if seed is None:
        seed = random.randint(0, 2**48)

    return {
        # 1. 加载 UNET 模型（从 diffusion_models 目录）
        "1": {
            "inputs": {
                "unet_name": "ltx-2-19b-dev-fp8.safetensors"
            },
            "class_type": "UNETLoader"
        },

        # 2. 加载图片
        "2": {
            "inputs": {
                "image": image_name
            },
            "class_type": "LoadImage"
        },

        # 3. 加载音频
        "3": {
            "inputs": {
                "audio": audio_name
            },
            "class_type": "LoadAudio"
        },

        # 4. 裁剪音频（添加缺失的 start_index）
        "4": {
            "inputs": {
                "audio": ["3", 0],
                "max_duration": 10,
                "duration": 10,
                "start_index": 0  # 新增必需参数
            },
            "class_type": "TrimAudioDuration"
        },

        # 5. 音频 VAE 加载器
        "5": {
            "inputs": {
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors"
            },
            "class_type": "LTXVAudioVAELoader"
        },

        # 6. 音频 VAE 编码
        "6": {
            "inputs": {
                "audio": ["4", 0],
                "audio_vae": ["5", 0]
            },
            "class_type": "LTXVAudioVAEEncode"
        },

        # 7. 图片预处理（添加缺失的 img_compression）
        "7": {
            "inputs": {
                "image": ["2", 0],
                "img_compression": 35  # 新增必需参数
            },
            "class_type": "LTXVPreprocess"
        },

        # 8. 空 Latent 视频
        "8": {
            "inputs": {
                "width": 768,
                "height": 512,
                "length": 121,  # ~5秒 @ 24fps
                "batch_size": 1
            },
            "class_type": "EmptyLTXVLatentVideo"
        },

        # 9. 视频 VAE（使用 UNET 的输出）
        "9": {
            "inputs": {},
            "class_type": "LTXVVideoVAELoader"
        },

        # 10. 图片转视频 Latent（添加缺失的参数）
        "10": {
            "inputs": {
                "vae": ["9", 0],
                "image": ["7", 0],
                "latent": ["8", 0],
                "strength": 1.0,     # 新增必需参数
                "bypass": False      # 新增必需参数
            },
            "class_type": "LTXVImgToVideoInplace"
        },

        # 11. 创建遮罩
        "11": {
            "inputs": {
                "value": 0,
                "width": 768,
                "height": 512
            },
            "class_type": "SolidMask"
        },

        # 12. 设置 Latent Noise Mask
        "12": {
            "inputs": {
                "samples": ["6", 0],
                "mask": ["11", 0]
            },
            "class_type": "SetLatentNoiseMask"
        },

        # 13. 连接音视频 Latent
        "13": {
            "inputs": {
                "video_latent": ["10", 0],
                "audio_latent": ["12", 0]
            },
            "class_type": "LTXVConcatAVLatent"
        },

        # 14. 简单的 KSampler
        "14": {
            "inputs": {
                "seed": seed,
                "steps": 20,
                "cfg": 3.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["13", 0],  # 使用连接后的 latent
                "negative": ["13", 0],  # 同样使用连接后的 latent
                "latent_image": ["13", 0]
            },
            "class_type": "KSampler"
        },

        # 15. 分离音视频 Latent
        "15": {
            "inputs": {
                "av_latent": ["14", 0]
            },
            "class_type": "LTXVSeparateAVLatent"
        },

        # 16. VAE 解码
        "16": {
            "inputs": {
                "samples": ["15", 0],
                "vae": ["9", 0]
            },
            "class_type": "LTXVVideoVAEDecode"
        },

        # 17. 视频合成输出
        "17": {
            "inputs": {
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "ltx2_minimal",
                "format": "video/h264-mp4",
                "images": ["16", 0],
                "audio": ["4", 0]
            },
            "class_type": "VHS_VideoCombine"
        }
    }

def main():
    print("=" * 70)
    print("LTX-2 Minimal Test - Fixed API Version")
    print("Using UNETLoader and corrected parameters")
    print("=" * 70)

    if not check_comfyui():
        return

    print("\n📁 Step 1: Uploading files...")
    try:
        image_name = upload_file('/workspace/ltx_test/test_input.jpg')
        audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    print("\n🔧 Step 2: Creating minimal workflow...")
    print("   📦 UNETLoader: ltx-2-19b-dev-fp8.safetensors")
    print("   🎵 Audio: Direct encoding (10 seconds)")
    print("   🖼️  Image: LTX preprocess (compression: 35)")
    print("   🎬 Generate: 121 frames @ 24fps (~5 seconds)")
    print("   💾 Output: H.264 MP4")

    workflow = create_minimal_workflow(image_name, audio_name)

    print("\n🚀 Step 3: Submitting to ComfyUI...")
    payload = {
        "prompt": workflow,
        "client_id": f"minimal_test_{int(time.time())}"
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
                    print(f"\n📋 Node errors:")
                    for node_id, error in result['node_errors'].items():
                        print(f"\n   Node {node_id} ({workflow[node_id]['class_type']}):")
                        if 'errors' in error:
                            for err in error['errors']:
                                print(f"      • {err.get('type')}: {err.get('details', err.get('message'))}")
                return

            prompt_id = result.get('prompt_id')
            print(f"✅ Success! Prompt ID: {prompt_id}")
            print("\n" + "=" * 70)
            print("🎬 VIDEO GENERATION STARTED!")
            print("=" * 70)
            print("\n⏱️  Expected time: ~2-5 minutes")
            print("\n📁 Output location:")
            print("   /workspace/ComfyUI/output/ltx2_minimal_*.mp4")
            print("\n📊 Monitor progress:")
            print("   curl -s localhost:8188/queue | python3 -m json.tool")
            print("\n🔍 Check output:")
            print("   ls -lht /workspace/ComfyUI/output/ | head -5")
            print("=" * 70)
            return prompt_id

    except request.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        error_body = e.read().decode('utf-8')
        print(f"\n📋 Response body:")
        try:
            error_data = json.loads(error_body)
            print(json.dumps(error_data, indent=2))
        except:
            print(error_body)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
