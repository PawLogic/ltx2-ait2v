#!/usr/bin/env python3
"""
LTX-2 API 快速测试脚本
"""
import requests
import json
import base64
import time
import os

# 配置
ENDPOINT_ID = "42qdgmzjc9ldy5"
API_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"

# 请设置您的 API Key
API_KEY = os.environ.get("RUNPOD_API_KEY", "YOUR_API_KEY_HERE")

# 测试资源 - 请替换为您的 URL
# 图片: 需要人脸正面照
# 音频: 需要语音音频 (MP3/WAV)
TEST_IMAGE_URL = "https://replicate.delivery/pbxt/KgU2n8P5FLzpRZbGVN86xB8wNcO0FpGRn0n8XVCXU7aKCZAF/person.jpg"
TEST_AUDIO_URL = "https://replicate.delivery/pbxt/Jt8rKKTLWKEBjOzVKJXjdPNuAWv9NbJqgPx2B1IvZrXOdqwE/audio.mp3"

def test_api():
    print("=" * 60)
    print("LTX-2 Serverless API 测试")
    print("=" * 60)
    print(f"Endpoint: {ENDPOINT_ID}")
    print(f"Image: {TEST_IMAGE_URL[:50]}...")
    print(f"Audio: {TEST_AUDIO_URL[:50]}...")
    print()

    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌ 请设置 RUNPOD_API_KEY 环境变量或修改脚本中的 API_KEY")
        print("   export RUNPOD_API_KEY='your-key-here'")
        return

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": {
            "image_url": TEST_IMAGE_URL,
            "audio_url": TEST_AUDIO_URL,
            "prompt_positive": "A person speaks naturally with perfect lip synchronization, high quality, detailed",
            "prompt_negative": "static, bad teeth, blurry, low quality, pixelated",
            "width": 1280,
            "height": 736,
            "quality_preset": "high"
        }
    }

    print("🚀 发送请求...")
    print(f"   质量: high (生产标准)")
    print(f"   分辨率: 1280x736")
    print()

    start_time = time.time()

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=660)
        elapsed = time.time() - start_time

        print(f"⏱️  响应时间: {elapsed:.1f}s")
        print()

        if response.status_code != 200:
            print(f"❌ HTTP 错误: {response.status_code}")
            print(response.text)
            return

        result = response.json()

        if result.get("status") == "success":
            output = result.get("output", {})
            print("=" * 60)
            print("✅ 生成成功!")
            print("=" * 60)
            print(f"   分辨率: {output.get('resolution')}")
            print(f"   时长: {output.get('duration')}")
            print(f"   帧数: {output.get('frames')} @ {output.get('fps')} fps")
            print(f"   质量: {output.get('quality_preset')}")
            print(f"   种子: {output.get('seed')}")
            print(f"   生成时间: {output.get('generation_time')}s")

            # 保存视频
            video_base64 = output.get("video_base64")
            if video_base64:
                filename = output.get("video_filename", f"test_output_{int(time.time())}.mp4")
                output_path = f"/Users/tangkaixin/Dev/LTX/test/{filename}"

                video_bytes = base64.b64decode(video_base64)
                with open(output_path, "wb") as f:
                    f.write(video_bytes)

                size_mb = len(video_bytes) / (1024 * 1024)
                print()
                print(f"📁 视频已保存: {output_path}")
                print(f"   大小: {size_mb:.2f} MB")

        elif result.get("status") == "error":
            print("=" * 60)
            print("❌ 生成失败!")
            print("=" * 60)
            print(f"   错误: {result.get('error')}")
            if result.get("traceback"):
                print(f"\n详细信息:\n{result.get('traceback')}")

        else:
            print("响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except requests.Timeout:
        print("❌ 请求超时 (>10分钟)")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
