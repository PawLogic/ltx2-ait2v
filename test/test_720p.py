k#!/usr/bin/env python3
"""
LTX-2 720P 测试 - 最终生产配置
1280x736, img_compression=30, 高质量首帧
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
    print("LTX-2 720P 最终生产配置测试")
    print("1280x736 + img_compression=30 + 高质量首帧")
    print("=" * 70)

    print("\n📁 步骤 1/3: 上传文件...")
    image_name = upload_file('/workspace/ltx_test/test_input.jpg')
    audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')

    print("\n🔧 步骤 2/3: 创建720P工作流...")
    print("   📦 CheckpointLoaderSimple: ltx-2-19b-dev-fp8.safetensors")
    print("   📝 LTXAVTextEncoderLoader: gemma_3_12B_it_fp8_scaled.safetensors")
    print("   📦 3个 LoRA 模型 (Distilled 0.6 + Detailer 1.0 + Camera 0.5)")
    print("   🎵 音频: 10秒完整")
    print("   🖼️  图片: 1280x736 (720P), img_compression=30 (高质量)")
    print("   🎬 输出: 297帧 @ 30fps = 9.9秒")
    print("   ⚙️  采样: 8步 + CFG 1.0")
    print("   💾 VAE: tile_size=640, overlap=80")

    seed = random.randint(0, 2**48)

    workflow = {
        "184": {
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
            "class_type": "CheckpointLoaderSimple"
        },
        "155": {
            "inputs": {
                "text_encoder": "gemma_3_12B_it_fp8_scaled.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
                "device": "default"
            },
            "class_type": "LTXAVTextEncoderLoader"
        },
        "171": {
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
            "class_type": "LTXVAudioVAELoader"
        },
        "288": {
            "inputs": {
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 0.6,
                "model": ["184", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        "290": {
            "inputs": {
                "lora_name": "ltx-2-19b-ic-lora-detailer.safetensors",
                "strength_model": 1.0,
                "model": ["288", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        "289": {
            "inputs": {
                "lora_name": "ltx-2-19b-lora-camera-control-dolly-in.safetensors",
                "strength_model": 0.5,
                "model": ["290", 0]
            },
            "class_type": "LoraLoaderModelOnly"
        },
        "240": {
            "inputs": {"image": image_name, "upload": "image"},
            "class_type": "LoadImage"
        },
        "243": {
            "inputs": {"audio": audio_name},
            "class_type": "LoadAudio"
        },
        "244": {
            "inputs": {
                "audio": ["243", 0],
                "max_duration": 15,
                "duration": 10,
                "start_index": 0
            },
            "class_type": "TrimAudioDuration"
        },
        "241": {
            "inputs": {
                "image": ["240", 0],
                "width": 1280,
                "height": 736,
                "upscale_method": "lanczos",
                "keep_proportion": "pad",
                "pad_color": "0, 0, 0",
                "crop_position": "center",
                "divisible_by": 32
            },
            "class_type": "ImageResizeKJv2"
        },
        "269": {
            "inputs": {
                "image": ["241", 0],
                "img_compression": 30
            },
            "class_type": "LTXVPreprocess"
        },
        "162": {
            "inputs": {
                "width": 1280,
                "height": 736,
                "length": 297,
                "batch_size": 1
            },
            "class_type": "EmptyLTXVLatentVideo"
        },
        "239": {
            "inputs": {
                "vae": ["184", 2],
                "image": ["269", 0],
                "latent": ["162", 0],
                "strength": 1.0,
                "bypass": False
            },
            "class_type": "LTXVImgToVideoInplace"
        },
        "242": {
            "inputs": {
                "audio": ["244", 0],
                "audio_vae": ["171", 0]
            },
            "class_type": "LTXVAudioVAEEncode"
        },
        "249": {
            "inputs": {"value": 0, "width": 1280, "height": 736},
            "class_type": "SolidMask"
        },
        "248": {
            "inputs": {
                "samples": ["242", 0],
                "mask": ["249", 0]
            },
            "class_type": "SetLatentNoiseMask"
        },
        "166": {
            "inputs": {
                "video_latent": ["239", 0],
                "audio_latent": ["248", 0]
            },
            "class_type": "LTXVConcatAVLatent"
        },
        "169": {
            "inputs": {
                "text": "A person speaks naturally with perfect lip synchronization, high quality, detailed",
                "clip": ["155", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "165": {
            "inputs": {
                "text": "static, bad teeth, blurry, low quality, pixelated, compressed",
                "clip": ["155", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "164": {
            "inputs": {
                "frame_rate": 30,
                "positive": ["169", 0],
                "negative": ["165", 0]
            },
            "class_type": "LTXVConditioning"
        },
        "178": {
            "inputs": {"noise_seed": seed, "randomize": "disable"},
            "class_type": "RandomNoise"
        },
        "154": {
            "inputs": {"sampler_name": "euler"},
            "class_type": "KSamplerSelect"
        },
        "238": {
            "inputs": {
                "scheduler": "simple",
                "steps": 8,
                "denoise": 1.0,
                "model": ["289", 0]
            },
            "class_type": "BasicScheduler"
        },
        "153": {
            "inputs": {
                "cfg": 1.0,
                "model": ["289", 0],
                "positive": ["164", 0],
                "negative": ["164", 1]
            },
            "class_type": "CFGGuider"
        },
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
        "245": {
            "inputs": {"av_latent": ["161", 0]},
            "class_type": "LTXVSeparateAVLatent"
        },
        "234": {
            "inputs": {
                "tile_size": 640,
                "overlap": 80,
                "temporal_size": 4096,
                "temporal_overlap": 8,
                "samples": ["245", 0],
                "vae": ["184", 2]
            },
            "class_type": "VAEDecodeTiled"
        },
        "190": {
            "inputs": {
                "frame_rate": 30,
                "loop_count": 0,
                "filename_prefix": "LTX2_720P",
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False,
                "pingpong": False,
                "save_output": True,
                "images": ["234", 0],
                "audio": ["244", 0]
            },
            "class_type": "VHS_VideoCombine"
        }
    }

    print("\n🚀 步骤 3/3: 提交工作流...")
    payload = {"prompt": workflow, "client_id": f"720p_test_{int(time.time())}"}
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
            print("🎬 720P 高质量视频生成中...")
            print("=" * 70)
            print(f"\n⏱️  预计: ~5-7分钟")
            print(f"📁 输出: /workspace/ComfyUI/output/LTX2_720P_*.mp4")
            print(f"🎯 分辨率: 1280x736 (720P标准)")
            print(f"💾 预计大小: 4-5MB (高质量)")
            print(f"\n⚠️  关键验证点:")
            print(f"   - 口型同步 (img_compression=30)")
            print(f"   - 首帧清晰度")
            print(f"   - 整体细节保留")
            print("\n" + "=" * 70)

            return prompt_id

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
