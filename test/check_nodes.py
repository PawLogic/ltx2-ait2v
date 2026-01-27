#!/usr/bin/env python3
"""
ComfyUI 节点检查工具
检查所有可用的节点类型，特别是 LTX 相关节点
"""
import json
from urllib import request

BASE_URL = "http://localhost:8188"

def check_nodes():
    print("=" * 70)
    print("ComfyUI Node Availability Checker")
    print("=" * 70)

    try:
        req = request.Request(f"{BASE_URL}/object_info")
        with request.urlopen(req, timeout=10) as resp:
            nodes = json.loads(resp.read())

        print(f"\n✅ Total nodes available: {len(nodes)}")

        # 检查关键节点
        critical_nodes = {
            "CheckpointLoaderSimple": "主模型加载器",
            "LTXAVTextEncoderLoader": "LTX 文本编码器",
            "LTXVAudioVAELoader": "LTX 音频 VAE",
            "LoraLoaderModelOnly": "LoRA 加载器",
            "LoadImage": "图片加载",
            "LoadAudio": "音频加载",
            "TrimAudioDuration": "音频裁剪",
            "ImageResizeKJv2": "图片调整",
            "LTXVPreprocess": "LTX 预处理",
            "CLIPTextEncode": "文本编码",
            "EmptyLTXVLatentVideo": "空 Latent 视频",
            "LTXVImgToVideoInplace": "图片转视频",
            "LTXVAudioVAEEncode": "音频 VAE 编码",
            "SolidMask": "遮罩创建",
            "SetLatentNoiseMask": "设置 Noise Mask",
            "LTXVConcatAVLatent": "连接音视频 Latent",
            "LTXVConditioning": "LTX 条件化",
            "RandomNoise": "随机噪声",
            "KSamplerSelect": "采样器选择",
            "BasicScheduler": "基础调度器",
            "CFGGuider": "CFG 引导",
            "SamplerCustomAdvanced": "高级采样器",
            "LTXVSeparateAVLatent": "分离音视频 Latent",
            "VAEDecodeTiled": "VAE 分块解码",
            "VHS_VideoCombine": "视频合成",
            "MelBandRoFormerModelLoader": "人声分离模型（可选）",
            "MelBandRoFormerSampler": "人声分离采样器（可选）"
        }

        print("\n📋 Critical Nodes Check:")
        print("-" * 70)
        missing_nodes = []
        optional_missing = []

        for node_type, description in critical_nodes.items():
            if node_type in nodes:
                print(f"✅ {node_type:35} - {description}")
            else:
                if "MelBand" in node_type:
                    print(f"⚠️  {node_type:35} - {description} (OPTIONAL)")
                    optional_missing.append(node_type)
                else:
                    print(f"❌ {node_type:35} - {description} (REQUIRED)")
                    missing_nodes.append(node_type)

        # LTX 相关节点
        print("\n🎬 All LTX-related Nodes:")
        print("-" * 70)
        ltx_nodes = sorted([k for k in nodes.keys() if 'LTX' in k.upper()])
        for node in ltx_nodes:
            print(f"   • {node}")

        # LoRA 相关
        print("\n📦 LoRA Nodes:")
        print("-" * 70)
        lora_nodes = sorted([k for k in nodes.keys() if 'lora' in k.lower()])
        for node in lora_nodes:
            print(f"   • {node}")

        # 视频相关
        print("\n🎥 Video Nodes:")
        print("-" * 70)
        video_nodes = sorted([k for k in nodes.keys() if 'video' in k.lower() or 'VHS' in k])
        for node in video_nodes:
            print(f"   • {node}")

        # 音频相关
        print("\n🎵 Audio Nodes:")
        print("-" * 70)
        audio_nodes = sorted([k for k in nodes.keys() if 'audio' in k.lower() and 'ltx' not in k.lower()])
        for node in audio_nodes:
            print(f"   • {node}")

        # 总结
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        if not missing_nodes:
            print("✅ All required nodes are available!")
        else:
            print(f"❌ Missing {len(missing_nodes)} required nodes:")
            for node in missing_nodes:
                print(f"   • {node}")

        if optional_missing:
            print(f"\n⚠️  Missing {len(optional_missing)} optional nodes:")
            for node in optional_missing:
                print(f"   • {node}")
            print("\n💡 Workflow will work without these nodes")
            print("   Use test_production_lite.py instead of test_production.py")

        if not missing_nodes:
            print("\n🚀 Ready to run:")
            if optional_missing:
                print("   python3 test_production_lite.py")
            else:
                print("   python3 test_production.py")

        print("=" * 70)

    except Exception as e:
        print(f"❌ Error checking nodes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_nodes()
