#!/usr/bin/env python3
"""
检查 VAE 相关节点
"""
import json
from urllib import request

BASE_URL = "http://localhost:8188"

def check_vae_nodes():
    try:
        req = request.Request(f"{BASE_URL}/object_info")
        with request.urlopen(req, timeout=10) as resp:
            nodes = json.loads(resp.read())

        print("=" * 70)
        print("VAE-related Nodes")
        print("=" * 70)

        # 查找所有 VAE 相关节点
        vae_nodes = sorted([k for k in nodes.keys() if 'vae' in k.lower()])

        print(f"\n📦 All VAE nodes ({len(vae_nodes)}):")
        for node in vae_nodes:
            print(f"   • {node}")

        # 重点检查 LTX VAE 节点
        print(f"\n🎬 LTX VAE nodes:")
        ltx_vae = [k for k in vae_nodes if 'ltx' in k.lower()]
        for node in ltx_vae:
            print(f"\n   • {node}")
            if node in nodes:
                print(f"     Inputs: {list(nodes[node].get('input', {}).get('required', {}).keys())}")

        # 检查通用 VAE Loader
        print(f"\n📦 VAELoader node:")
        if "VAELoader" in nodes:
            print("   ✅ VAELoader exists")
            print(f"   Parameters: {nodes['VAELoader'].get('input', {})}")
        else:
            print("   ❌ VAELoader not found")

        # 检查 VAEDecode
        print(f"\n📦 VAEDecode nodes:")
        decode_nodes = [k for k in nodes.keys() if 'vaedecode' in k.lower()]
        for node in decode_nodes:
            print(f"   • {node}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_vae_nodes()
