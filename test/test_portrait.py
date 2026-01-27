#!/usr/bin/env python3
"""
LTX-2 竖屏测试 - 736x1280
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
    print("LTX-2 竖屏测试 (Portrait Mode)")
    print("736x1280 @ 30fps, 297帧, 9.9秒")
    print("=" * 70)

    print("\n📁 步骤 1/3: 上传文件...")
    image_name = upload_file('/workspace/ltx_test/test_input.jpg')
    audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')

    print("\n🔧 步骤 2/3: 加载竖屏工作流...")

    # 加载生成的竖屏workflow
    with open('/workspace/ltx_test/workflow_portrait_test.json') as f:
        workflow = json.load(f)

    # 转换为字符串以替换占位符
    workflow_str = json.dumps(workflow)

    seed = random.randint(0, 2**48)

    # 替换占位符
    replacements = {
        'INPUT_IMAGE': image_name,
        'INPUT_AUDIO': audio_name,
        'PROMPT_POSITIVE': 'A person speaks naturally in portrait mode, vertical video',
        'PROMPT_NEGATIVE': 'blurry, low quality, horizontal, landscape',
        'SEED': str(seed),
        'WIDTH': '736',
        'HEIGHT': '1280',
        'NUM_FRAMES': '297',
        'FPS': '30',
        'AUDIO_DURATION': '10',
        'STEPS': '8',
        'CFG_SCALE': '1.0',
        'LORA_DISTILLED_STRENGTH': '0.6',
        'LORA_DETAILER_STRENGTH': '1.0',
        'LORA_CAMERA_STRENGTH': '0.5'
    }

    for key, value in replacements.items():
        workflow_str = workflow_str.replace(key, value)

    workflow = json.loads(workflow_str)

    print("   📱 竖屏分辨率: 736x1280")
    print("   🎬 帧数: 297帧 @ 30fps = 9.9秒")
    print("   🎵 音频: 10秒")
    print("   ⚙️  img_compression: 20")
    print("   💾 tile_size: 640, overlap: 80")

    print("\n🚀 步骤 3/3: 提交工作流...")
    payload = {"prompt": workflow, "client_id": f"portrait_test_{int(time.time())}"}
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
            print("📱 竖屏视频生成中...")
            print("=" * 70)
            print(f"\n⏱️  预计: ~7分钟")
            print(f"📁 输出: /workspace/ComfyUI/output/ltx2_output_*.mp4")
            print(f"📐 分辨率: 736x1280 (竖屏9:16)")
            print(f"💾 预计大小: ~5-6MB")
            print(f"\n⚠️  验证点:")
            print(f"   - 竖屏方向正确")
            print(f"   - 口型同步完美")
            print(f"   - 质量与横屏相当")
            print("\n" + "=" * 70)

            return prompt_id

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
