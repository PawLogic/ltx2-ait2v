#!/usr/bin/env python3
"""
诊断脚本：检查模型文件位置和节点参数
"""
import json
from urllib import request
import os

BASE_URL = "http://localhost:8188"

def check_model_files():
    """检查文件系统中的模型文件"""
    print("=" * 70)
    print("🔍 Checking Model Files on Filesystem")
    print("=" * 70)

    model_paths = [
        "/workspace/ComfyUI/models/checkpoints",
        "/workspace/ComfyUI/models/diffusion_models",
        "/workspace/ComfyUI/models/unet",
        "/workspace/models",  # Network volume
        "/workspace/ltx-models",
    ]

    ltx_files = []
    for path in model_paths:
        if os.path.exists(path):
            print(f"\n📁 {path}")
            try:
                files = os.listdir(path)
                for f in sorted(files):
                    if 'ltx' in f.lower() or 'safetensors' in f.lower():
                        full_path = os.path.join(path, f)
                        size = os.path.getsize(full_path) / (1024**3)  # GB
                        print(f"   ✅ {f} ({size:.2f} GB)")
                        ltx_files.append((path, f, size))
                if not any('ltx' in f.lower() or 'safetensors' in f.lower() for f in files):
                    print(f"   ⚠️  No LTX or safetensors files found")
            except Exception as e:
                print(f"   ❌ Error reading directory: {e}")
        else:
            print(f"\n📁 {path} - NOT FOUND")

    return ltx_files

def check_comfyui_models():
    """检查 ComfyUI API 返回的可用模型"""
    print("\n" + "=" * 70)
    print("🔍 Checking Models Available in ComfyUI API")
    print("=" * 70)

    try:
        req = request.Request(f"{BASE_URL}/object_info")
        with request.urlopen(req, timeout=10) as resp:
            nodes = json.loads(resp.read())

        # CheckpointLoaderSimple
        if "CheckpointLoaderSimple" in nodes:
            checkpoint_node = nodes["CheckpointLoaderSimple"]
            if "input" in checkpoint_node and "required" in checkpoint_node["input"]:
                ckpt_config = checkpoint_node["input"]["required"].get("ckpt_name", [])
                if ckpt_config and len(ckpt_config) > 0:
                    checkpoints = ckpt_config[0]
                    print(f"\n📦 CheckpointLoaderSimple - Available checkpoints ({len(checkpoints)}):")
                    for ckpt in sorted(checkpoints)[:10]:  # 只显示前10个
                        print(f"   • {ckpt}")
                    if len(checkpoints) > 10:
                        print(f"   ... and {len(checkpoints) - 10} more")
                else:
                    print(f"\n❌ CheckpointLoaderSimple - No checkpoints available!")

        # LTXVAudioVAELoader
        if "LTXVAudioVAELoader" in nodes:
            vae_node = nodes["LTXVAudioVAELoader"]
            print(f"\n📦 LTXVAudioVAELoader parameters:")
            print(json.dumps(vae_node.get("input", {}), indent=2))

        # LTXAVTextEncoderLoader
        if "LTXAVTextEncoderLoader" in nodes:
            encoder_node = nodes["LTXAVTextEncoderLoader"]
            print(f"\n📦 LTXAVTextEncoderLoader parameters:")
            print(json.dumps(encoder_node.get("input", {}), indent=2))

        # ImageResizeKJv2
        if "ImageResizeKJv2" in nodes:
            resize_node = nodes["ImageResizeKJv2"]
            print(f"\n📦 ImageResizeKJv2 parameters:")
            print(json.dumps(resize_node.get("input", {}), indent=2))

        # LTXVPreprocess
        if "LTXVPreprocess" in nodes:
            preprocess_node = nodes["LTXVPreprocess"]
            print(f"\n📦 LTXVPreprocess parameters:")
            print(json.dumps(preprocess_node.get("input", {}), indent=2))

        # LTXVImgToVideoInplace
        if "LTXVImgToVideoInplace" in nodes:
            img2vid_node = nodes["LTXVImgToVideoInplace"]
            print(f"\n📦 LTXVImgToVideoInplace parameters:")
            print(json.dumps(img2vid_node.get("input", {}), indent=2))

        return nodes

    except Exception as e:
        print(f"❌ Error fetching node info: {e}")
        return None

def suggest_fix(ltx_files, nodes):
    """根据诊断结果提供修复建议"""
    print("\n" + "=" * 70)
    print("💡 Suggested Fixes")
    print("=" * 70)

    if not ltx_files:
        print("\n❌ CRITICAL: No LTX model files found!")
        print("\n📥 You need to download the model first:")
        print("   1. Check network volume: ls -lh /workspace/models/")
        print("   2. Or run model downloader from your deployment guide")
        print("   3. Model should be ~19GB: ltx-2-19b-dev-fp8.safetensors")
    else:
        print(f"\n✅ Found {len(ltx_files)} LTX-related files:")
        for path, filename, size in ltx_files:
            print(f"   • {filename} in {path} ({size:.2f} GB)")

        print("\n💡 Model files exist but ComfyUI can't find them.")
        print("   Possible fixes:")
        print("   1. Check if files are in correct directory:")
        print("      - Checkpoints: /workspace/ComfyUI/models/checkpoints/")
        print("      - Diffusion: /workspace/ComfyUI/models/diffusion_models/")
        print("      - Unet: /workspace/ComfyUI/models/unet/")
        print("   2. Create symlinks if files are in network volume:")
        for path, filename, size in ltx_files:
            if '/workspace/models' in path or '/workspace/ltx-models' in path:
                print(f"      ln -s {os.path.join(path, filename)} /workspace/ComfyUI/models/checkpoints/{filename}")
        print("   3. Restart ComfyUI after moving/linking files")

    if nodes:
        print("\n📋 Node parameter mismatches detected.")
        print("   The workflow was created with an older API version.")
        print("   I'll create a simplified workflow that uses current API.")

if __name__ == "__main__":
    ltx_files = check_model_files()
    nodes = check_comfyui_models()
    suggest_fix(ltx_files, nodes)
