#!/usr/bin/env python3
"""
LTX-2 生产级完整测试脚本
基于 workflow_api_format.json 的真实工作流
包含所有节点：LoRA、人声提取、图片预处理、完整生成流程
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

def create_full_workflow(image_name, audio_name, seed=None):
    """
    创建完整的生产级工作流
    基于 workflow_api_format.json
    """
    if seed is None:
        seed = random.randint(0, 2**48)

    return {
        # 主模型加载
        "184": {
            "inputs": {
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        # 文本编码器加载
        "155": {
            "inputs": {
                "t5_model": "gemma_3_12B_it_fp8_scaled.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
                "precision": "default"
            },
            "class_type": "LTXAVTextEncoderLoader"
        },
        # 音频 VAE 加载
        "171": {
            "inputs": {
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors"
            },
            "class_type": "LTXVAudioVAELoader"
        },
        # MelBandRoformer 人声提取模型
        "272": {
            "inputs": {
                "model_name": "MelBandRoformer_fp16.safetensors"
            },
            "class_type": "MelBandRoFormerModelLoader"
        },
        # LoRA 1: Distilled
        "288": {
            "inputs": {
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 0.6,
                "model": ["184", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        # LoRA 2: Detailer
        "290": {
            "inputs": {
                "lora_name": "ltx-2-19b-ic-lora-detailer.safetensors",
                "strength_model": 1.0,
                "model": ["288", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        # LoRA 3: Camera Control
        "289": {
            "inputs": {
                "lora_name": "ltx-2-19b-lora-camera-control-dolly-in.safetensors",
                "strength_model": 0.5,
                "model": ["290", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        # 加载图片
        "240": {
            "inputs": {
                "image": image_name,
                "upload": "image"
            },
            "class_type": "LoadImage"
        },
        # 加载音频
        "243": {
            "inputs": {
                "audio": audio_name,
                "upload": "audio"
            },
            "class_type": "LoadAudio"
        },
        # 裁剪音频到10秒
        "244": {
            "inputs": {
                "max_duration": 10,
                "duration": 10,
                "audio": ["243", 0]
            },
            "class_type": "TrimAudioDuration"
        },
        # 提取人声
        "271": {
            "inputs": {
                "model": ["272", 0],
                "audio": ["244", 0]
            },
            "class_type": "MelBandRoFormerSampler"
        },
        # 调整图片尺寸
        "241": {
            "inputs": {
                "width": 768,
                "height": 512,
                "upscale_method": "lanczos",
                "crop": "pad_edge",
                "pad_fill": "0, 0, 0",
                "align": "center",
                "divisor": 2,
                "device": "cpu",
                "image": ["240", 0]
            },
            "class_type": "ImageResizeKJv2"
        },
        # LTX 图片预处理
        "269": {
            "inputs": {
                "strength": 42,
                "image": ["241", 0]
            },
            "class_type": "LTXVPreprocess"
        },
        # 正向提示词
        "169": {
            "inputs": {
                "text": "A person speaks naturally with perfect lip synchronization to the audio. Expressive facial movements, natural eye contact with the camera. Professional studio lighting, cinematic quality, high detail.",
                "clip": ["155", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        # 负向提示词
        "165": {
            "inputs": {
                "text": "static, bad teeth, deformed teeth, blurry, overexposed, underexposed, low contrast, artifacts, distorted, disfigured",
                "clip": ["155", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        # 空 latent 视频
        "162": {
            "inputs": {
                "width": 768,
                "height": 512,
                "length": 297,
                "batch_size": 1
            },
            "class_type": "EmptyLTXVLatentVideo"
        },
        # 图片转视频 latent
        "239": {
            "inputs": {
                "start_frame": 1,
                "end_at_last": False,
                "vae": ["184", 2],
                "image": ["269", 0],
                "latent": ["162", 0]
            },
            "class_type": "LTXVImgToVideoInplace"
        },
        # 音频 VAE 编码
        "242": {
            "inputs": {
                "audio": ["271", 0],
                "audio_vae": ["171", 0]
            },
            "class_type": "LTXVAudioVAEEncode"
        },
        # 创建遮罩
        "249": {
            "inputs": {
                "value": 0,
                "width": 768,
                "height": 512
            },
            "class_type": "SolidMask"
        },
        # 设置 latent noise mask
        "248": {
            "inputs": {
                "samples": ["242", 0],
                "mask": ["249", 0]
            },
            "class_type": "SetLatentNoiseMask"
        },
        # 连接音视频 latent
        "166": {
            "inputs": {
                "video_latent": ["239", 0],
                "audio_latent": ["248", 0]
            },
            "class_type": "LTXVConcatAVLatent"
        },
        # LTX 条件化
        "164": {
            "inputs": {
                "frame_rate": 30,
                "positive": ["169", 0],
                "negative": ["165", 0]
            },
            "class_type": "LTXVConditioning"
        },
        # 随机噪声
        "178": {
            "inputs": {
                "noise_seed": seed
            },
            "class_type": "RandomNoise"
        },
        # 采样器选择
        "154": {
            "inputs": {
                "sampler_name": "euler"
            },
            "class_type": "KSamplerSelect"
        },
        # 调度器
        "238": {
            "inputs": {
                "scheduler": "simple",
                "steps": 8,
                "denoise": 1.0,
                "model": ["289", 0]
            },
            "class_type": "BasicScheduler"
        },
        # CFG 引导
        "153": {
            "inputs": {
                "cfg": 1.0,
                "model": ["289", 0],
                "positive": ["164", 0],
                "negative": ["164", 1]
            },
            "class_type": "CFGGuider"
        },
        # 高级采样器
        "161": {
            "inputs": {
                "noise": ["178", 0],
                "guider": ["153", 0],
                "sampler": ["154", 0],
                "sigmas": ["238", 0],
                "latent_image": ["166", 0]
            },
            "class_type": "SamplerCustomAdvanced"
        },
        # 分离音视频 latent
        "245": {
            "inputs": {
                "av_latent": ["161", 0]
            },
            "class_type": "LTXVSeparateAVLatent"
        },
        # VAE 分块解码
        "234": {
            "inputs": {
                "tile_size": 512,
                "overlap": 64,
                "temporal_size": 4096,
                "temporal_overlap": 8,
                "samples": ["245", 0],
                "vae": ["184", 2]
            },
            "class_type": "VAEDecodeTiled"
        },
        # 视频合成输出
        "190": {
            "inputs": {
                "frame_rate": 30,
                "loop_count": 0,
                "filename_prefix": "ltx2_output",
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": True,
                "pingpong": False,
                "save_output": True,
                "images": ["234", 0],
                "audio": ["244", 0]
            },
            "class_type": "VHS_VideoCombine"
        }
    }

def main():
    print("=" * 70)
    print("LTX-2 Production Test - Full Workflow")
    print("Based on workflow_api_format.json")
    print("=" * 70)

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

    # 创建完整工作流
    print("\n🔧 Step 2: Creating production workflow...")
    print("   📦 Loading: Checkpoint + 3 LoRAs")
    print("   🎵 Audio: MelBandRoformer vocal extraction")
    print("   🖼️  Image: Resize + LTX preprocess")
    print("   🎬 Generate: 297 frames @ 30fps (~10 seconds)")
    print("   💾 Output: H.264 MP4 with audio")

    workflow = create_full_workflow(image_name, audio_name)

    print("\n🚀 Step 3: Submitting to ComfyUI...")
    payload = {
        "prompt": workflow,
        "client_id": f"production_test_{int(time.time())}"
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
                        print(f"   Node {node_id}: {error}")
                return

            prompt_id = result.get('prompt_id')
            print(f"✅ Success! Prompt ID: {prompt_id}")
            print("\n" + "=" * 70)
            print("🎬 FULL PRODUCTION WORKFLOW STARTED!")
            print("=" * 70)
            print("\n⏱️  Expected time: ~3-8 minutes (depends on GPU)")
            print("\n📊 Workflow includes:")
            print("   • Checkpoint: ltx-2-19b-dev-fp8.safetensors")
            print("   • LoRAs: Distilled (0.6) + Detailer (1.0) + Camera (0.5)")
            print("   • Audio: Vocal extraction with MelBandRoformer")
            print("   • Video: 768x512, 297 frames, 30fps")
            print("   • Quality: CRF 19 (high quality)")
            print("\n📊 Monitor progress:")
            print("   curl -s localhost:8188/queue | python3 -m json.tool")
            print("\n📁 Output location:")
            print("   /workspace/ComfyUI/output/ltx2_output_*.mp4")
            print("\n🔍 Check outputs:")
            print("   ls -lht /workspace/ComfyUI/output/ | head -5")
            print("\n💡 Watch queue in real-time:")
            print("   watch -n 2 'curl -s localhost:8188/queue | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"Running: {len(d.get(\\\\\\\"queue_running\\\\\\\",[]))}, Pending: {len(d.get(\\\\\\\"queue_pending\\\\\\\",[]))}\\\")'")
            print("=" * 70)
            return prompt_id

    except request.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        error_body = e.read().decode('utf-8')
        print(f"\n📋 Response body:")
        print(error_body)
        try:
            error_data = json.loads(error_body)
            if 'error' in error_data:
                print(f"\n❌ Error detail: {error_data['error']}")
            if 'node_errors' in error_data:
                print(f"\n📋 Node errors:")
                for node_id, error in error_data['node_errors'].items():
                    print(f"   Node {node_id}: {error}")
        except:
            pass
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
