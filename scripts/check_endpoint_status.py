#!/usr/bin/env python3
"""检查 RunPod Serverless Endpoint 状态"""

import os
import sys
import json
import requests

# API 配置 - 从环境变量读取
API_KEY = os.environ.get("RUNPOD_API_KEY", "")
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "42qdgmzjc9ldy5")

def main():
    if not API_KEY:
        print("❌ 错误: 请设置 RUNPOD_API_KEY 环境变量")
        print("   export RUNPOD_API_KEY=your_api_key")
        return 1

    print("=" * 70)
    print("RunPod Serverless Endpoint 状态检查")
    print("=" * 70)

    try:
        # 健康检查
        print("\n正在检查 Endpoint 健康状态...")
        response = requests.get(
            f"https://api.runpod.ai/v2/{ENDPOINT_ID}/health",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        health = response.json()

        print(f"\n✅ Endpoint ID: {ENDPOINT_ID}")
        print(f"   Workers 状态:")
        print(f"   - Ready: {health.get('workers', {}).get('ready', 0)}")
        print(f"   - Running: {health.get('workers', {}).get('running', 0)}")
        print(f"   - Idle: {health.get('workers', {}).get('idle', 0)}")

        # 完整响应
        print(f"\n完整响应:")
        print(json.dumps(health, indent=2))

        # 诊断
        workers = health.get('workers', {})
        if workers.get('ready', 0) == 0:
            print("\n⚠️ 警告: 没有 ready workers")
            print("   可能的原因:")
            print("   1. Network Volume 上缺少模型文件")
            print("   2. Worker 初始化失败")
            print("   3. Docker 镜像配置错误")
        else:
            print(f"\n✅ 状态正常: {workers.get('ready')} workers ready")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
