#!/usr/bin/env python3
"""
LTX-2 完整功能测试 - SSH 版本
使用所有可用模型：主模型 + 3个LoRA
"""
import json
import time
import random
from urllib import request
import os

BASE_URL = "http://localhost:8188"

def upload_file(filepath):
    filename = os.path.basename(filepath)
    print(f"📤 上传 {filename}...")
    with open(filepath, 'rb') as f:
        data = f.read()
    boundary = 'Boundary' + ''.join(random.choices('0123456789', k=16))
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    ).encode() + data + f'\r\n--{boundary}--\r\n'.encode()
    req = request.Request(f"{BASE_URL}/upload/image", data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        print(f"   ✅ {result.get('name')}")
        return result.get('name')

def monitor_progress(prompt_id):
    """监控生成进度"""
    print("\n📊 监控生成进度...")
    last_status = None
    while True:
        try:
            req = request.Request(f"{BASE_URL}/history/{prompt_id}")
            with request.urlopen(req, timeout=5) as resp:
                history = json.loads(resp.read())
                if prompt_id in history:
                    status_info = history[prompt_id]
                    if 'outputs' in status_info and status_info['outputs']:
                        print("\n✅ 生成完成!")
                        return status_info
                    status = status_info.get('status', {})
                    if status != last_status:
                        print(f"   状态: {status}")
                        last_status = status
        except:
            pass

        # 检查队列
        try:
            req = request.Request(f"{BASE_URL}/queue")
            with request.urlopen(req, timeout=5) as resp:
                queue = json.loads(resp.read())
                running = len(queue.get('queue_running', []))
                pending = len(queue.get('queue_pending', []))
                if running == 0 and pending == 0:
                    time.sleep(5)  # 等待输出写入
                    return None
                print(f"   队列: 运行中={running}, 等待中={pending}", end='\r')
        except:
            pass

        time.sleep(3)

def main():
    print("=" * 70)
    print("LTX-2 完整功能测试")
    print("主模型 + 3个LoRA + 音频驱动视频生成")
    print("=" * 70)

    # 上传文件
    print("\n📁 步骤 1/3: 上传测试文件...")
    image_name = upload_file('/workspace/ltx_test/test_input.jpg')
    audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')

    # 创建工作流
    print("\n🔧 步骤 2/3: 创建完整工作流...")
    print("   📦 主模型: ltx-2-19b-dev-fp8.safetensors (26GB)")
    print("   📦 LoRA 1: Distilled (强度 0.6)")
    print("   📦 LoRA 2: Detailer (强度 1.0)")
    print("   📦 LoRA 3: Camera Control (强度 0.5)")
    print("   🎵 音频: 5秒片段")
    print("   🖼️  图片: 768x512 (自动调整)")
    print("   🎬 输出: 121帧 @ 24fps (~5秒视频)")

    seed = random.randint(0, 2**48)

    workflow = {
        "1": {
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 0.6,
                "model": ["1", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        "3": {
            "inputs": {
                "lora_name": "ltx-2-19b-ic-lora-detailer.safetensors",
                "strength_model": 1.0,
                "model": ["2", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        "4": {
            "inputs": {
                "lora_name": "ltx-2-19b-lora-camera-control-dolly-in.safetensors",
                "strength_model": 0.5,
                "model": ["3", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        "5": {
            "inputs": {"image": image_name},
            "class_type": "LoadImage"
        },
        "6": {
            "inputs": {"audio": audio_name},
            "class_type": "LoadAudio"
        },
        "7": {
            "inputs": {
                "audio": ["6", 0],
                "max_duration": 10,
                "duration": 5,
                "start_index": 0
            },
            "class_type": "TrimAudioDuration"
        },
        "8": {
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
            "class_type": "LTXVAudioVAELoader"
        },
        "9": {
            "inputs": {
                "audio": ["7", 0],
                "audio_vae": ["8", 0]
            },
            "class_type": "LTXVAudioVAEEncode"
        },
        "10": {
            "inputs": {
                "image": ["5", 0],
                "width": 768,
                "height": 512,
                "upscale_method": "lanczos",
                "keep_proportion": "pad",
                "pad_color": "0, 0, 0",
                "crop_position": "center",
                "divisible_by": 32
            },
            "class_type": "ImageResizeKJv2"
        },
        "11": {
            "inputs": {
                "image": ["10", 0],
                "img_compression": 35
            },
            "class_type": "LTXVPreprocess"
        },
        "12": {
            "inputs": {
                "width": 768,
                "height": 512,
                "length": 121,
                "batch_size": 1
            },
            "class_type": "EmptyLTXVLatentVideo"
        },
        "13": {
            "inputs": {
                "vae": ["1", 2],
                "image": ["11", 0],
                "latent": ["12", 0],
                "strength": 1.0,
                "bypass": False
            },
            "class_type": "LTXVImgToVideoInplace"
        },
        "14": {
            "inputs": {
                "value": 0,
                "width": 768,
                "height": 512
            },
            "class_type": "SolidMask"
        },
        "15": {
            "inputs": {
                "samples": ["9", 0],
                "mask": ["14", 0]
            },
            "class_type": "SetLatentNoiseMask"
        },
        "16": {
            "inputs": {
                "video_latent": ["13", 0],
                "audio_latent": ["15", 0]
            },
            "class_type": "LTXVConcatAVLatent"
        },
        "17": {
            "inputs": {
                "seed": seed,
                "steps": 20,
                "cfg": 1.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["16", 0],
                "negative": ["16", 0],
                "latent_image": ["16", 0]
            },
            "class_type": "KSampler"
        },
        "18": {
            "inputs": {"av_latent": ["17", 0]},
            "class_type": "LTXVSeparateAVLatent"
        },
        "19": {
            "inputs": {
                "tile_size": 512,
                "overlap": 64,
                "temporal_size": 4096,
                "temporal_overlap": 8,
                "samples": ["18", 0],
                "vae": ["1", 2]
            },
            "class_type": "VAEDecodeTiled"
        },
        "20": {
            "inputs": {
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "ltx2_full_test",
                "format": "video/h264-mp4",
                "images": ["19", 0],
                "audio": ["7", 0]
            },
            "class_type": "VHS_VideoCombine"
        }
    }

    # 提交工作流
    print("\n🚀 步骤 3/3: 提交并生成...")
    payload = {"prompt": workflow, "client_id": f"full_test_{int(time.time())}"}
    req = request.Request(f"{BASE_URL}/prompt",
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})

    try:
        with request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if 'error' in result:
                print(f"\n❌ 工作流错误:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return None

            prompt_id = result.get('prompt_id')
            print(f"✅ 工作流已提交! ID: {prompt_id}")
            print("\n" + "=" * 70)

            # 监控进度
            result = monitor_progress(prompt_id)

            if result:
                print("\n📁 查找输出文件...")
                import subprocess
                files = subprocess.check_output(
                    "ls -lt /workspace/ComfyUI/output/*.mp4 2>/dev/null | head -5",
                    shell=True
                ).decode()
                print(files)

                print("\n" + "=" * 70)
                print("🎉 视频生成完成!")
                print("=" * 70)
                print("\n📂 输出目录: /workspace/ComfyUI/output/")
                print("🎬 文件名: ltx2_full_test_*.mp4")

                return prompt_id
            else:
                print("\n⚠️  生成可能失败，请检查日志")
                return None

    except request.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"\n❌ HTTP 错误 {e.code}")
        try:
            print(json.dumps(json.loads(error_body), indent=2, ensure_ascii=False))
        except:
            print(error_body)
        return None
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
