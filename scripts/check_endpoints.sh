#!/bin/bash
# 检查所有 RunPod Serverless Endpoints
# 需要设置环境变量: export RUNPOD_API_KEY=your_api_key

if [ -z "$RUNPOD_API_KEY" ]; then
  echo "❌ 错误: 请设置 RUNPOD_API_KEY 环境变量"
  echo "   export RUNPOD_API_KEY=your_api_key"
  exit 1
fi

curl -s -X POST https://api.runpod.ai/graphql \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { myself { endpoints { id name gpuIds templateId networkVolumeId workersMin workersMax idleTimeout scalerType scalerValue } } }"
  }' | python3 -m json.tool
