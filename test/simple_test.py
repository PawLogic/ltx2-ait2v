#!/usr/bin/env python3
"""Simple ComfyUI API test"""
import json
from urllib import request

BASE_URL = "http://localhost:8188"

try:
    # Test 1: System stats
    print("1. Testing /system_stats...")
    req = request.Request(f"{BASE_URL}/system_stats")
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        print(f"   ✅ System: {data.get('system', {}).get('os', 'unknown')}")
        print(f"   VRAM: {data.get('devices', [{}])[0].get('vram_total', 0) / 1024**3:.1f} GB")

    # Test 2: Object info (LTX nodes)
    print("\n2. Testing /object_info...")
    req = request.Request(f"{BASE_URL}/object_info")
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        ltx_nodes = [k for k in data.keys() if 'LTX' in k.upper()]
        print(f"   ✅ Found {len(ltx_nodes)} LTX nodes")
        for node in ltx_nodes[:5]:
            print(f"      - {node}")

    # Test 3: Queue status
    print("\n3. Testing /queue...")
    req = request.Request(f"{BASE_URL}/queue")
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        running = len(data.get('queue_running', []))
        pending = len(data.get('queue_pending', []))
        print(f"   ✅ Queue: {running} running, {pending} pending")

    # Test 4: Check models
    print("\n4. Testing model detection...")
    req = request.Request(f"{BASE_URL}/object_info")
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        if 'CheckpointLoaderSimple' in data:
            checkpoints = data['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
            print(f"   ✅ Found {len(checkpoints)} checkpoint(s)")
            for ckpt in checkpoints:
                if 'ltx' in ckpt.lower():
                    print(f"      - {ckpt}")

    print("\n✅ All API tests passed!")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
