#!/usr/bin/env python3
"""
LTX-2 完整功能测试 - 修正版
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

def main():
    print("=" * 70)
    print("LTX-2 完整功能测试 - 修正版")
    print("=" * 70)

    print("\n📁 步骤 1/3: 上传测试文件...")
    image_name = upload_file('/workspace/ltx_test/test_input.jpg')
    audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')

    print("\n🔧 步骤 2/3: 创建工作流...")
    print("   📦 主模型 + 3个LoRA")
    print("   🎵 音频: 5秒")
    print("   🖼️  图片: 768x512")
    print("   🎬 输出: 121帧 @ 24fps")

    seed = random.randint(0, 2**48)

    workflow = {
        # 1. Checkpoint
        "1": {
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
            "class_type": "CheckpointLoaderSimple"
        },
        # 2-4. LoRAs
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
        # 5-7. 文件加载
        "5": {"inputs": {"image": image_name}, "class_type": "LoadImage"},
        "6": {"inputs": {"audio": audio_name}, "class_type": "LoadAudio"},
        "7": {
            "inputs": {
                "audio": ["6", 0],
                "max_duration": 10,
                "duration": 5,
                "start_index": 0
            },
            "class_type": "TrimAudioDuration"
        },
        # 8-9. 音频处理
        "8": {
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
            "class_type": "LTXVAudioVAELoader"
        },
        "9": {
            "inputs": {"audio": ["7", 0], "audio_vae": ["8", 0]},
            "class_type": "LTXVAudioVAEEncode"
        },
        # 10-11. 图片处理
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
            "inputs": {"image": ["10", 0], "img_compression": 35},
            "class_type": "LTXVPreprocess"
        },
        # 12-13. Latent 准备
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
        # 14-16. 音视频合并
        "14": {
            "inputs": {"value": 0, "width": 768, "height": 512},
            "class_type": "SolidMask"
        },
        "15": {
            "inputs": {"samples": ["9", 0], "mask": ["14", 0]},
            "class_type": "SetLatentNoiseMask"
        },
        "16": {
            "inputs": {
                "video_latent": ["13", 0],
                "audio_latent": ["15", 0]
            },
            "class_type": "LTXVConcatAVLatent"
        },
        # 17-18. 创建简单的 Conditioning
        "17": {
            "inputs": {
                "text": "a person speaking naturally",
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "18": {
            "inputs": {
                "text": "",
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        # 19. KSampler
        "19": {
            "inputs": {
                "seed": seed,
                "steps": 20,
                "cfg": 1.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["17", 0],  # 使用 CLIP 编码的文本
                "negative": ["18", 0],  # 使用空文本
                "latent_image": ["16", 0]
            },
            "class_type": "KSampler"
        },
        # 20-22. 解码和输出
        "20": {
            "inputs": {"av_latent": ["19", 0]},
            "class_type": "LTXVSeparateAVLatent"
        },
        "21": {
            "inputs": {
                "tile_size": 512,
                "overlap": 64,
                "temporal_size": 4096,
                "temporal_overlap": 8,
                "samples": ["20", 0],
                "vae": ["1", 2]
            },
            "class_type": "VAEDecodeTiled"
        },
        "22": {
            "inputs": {
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "ltx2_full",
                "format": "video/h264-mp4",
                "save_output": True,  # 新增
                "pingpong": False,    # 新增
                "images": ["21", 0],
                "audio": ["7", 0]
            },
            "class_type": "VHS_VideoCombine"
        }
    }

    print("\n🚀 步骤 3/3: 提交工作流...")
    payload = {"prompt": workflow, "client_id": f"test_{int(time.time())}"}
    req = request.Request(f"{BASE_URL}/prompt",
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})

    try:
        with request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if 'error' in result:
                print(f"\n❌ 错误:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return None

            prompt_id = result.get('prompt_id')
            print(f"✅ 已提交! ID: {prompt_id}")
            print("\n" + "=" * 70)
            print("🎬 视频生成中...")
            print("=" * 70)
            print(f"\n⏱️  预计: ~3-5分钟")
            print(f"📁 输出: /workspace/ComfyUI/output/ltx2_full_*.mp4")
            print("\n💡 监控进度:")
            print("   curl -s localhost:8188/queue | python3 -m json.tool")
            print("\n" + "=" * 70)

            return prompt_id

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
